#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct https_event_t {
    __u32 pid;
    __u32 tid;
    __u64 timestamp_ns;
    __u64 duration_ns;
    char  comm[16];
    char  phase[16];   // "write_enter" or "read_return"
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 24); // 16MB
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 8192);
} start_times SEC(".maps");

// Fires before TLS write. We only record metadata, not payload content.
SEC("uprobe/libssl.so:SSL_write")
int trace_ssl_write_entry(struct pt_regs *ctx) {
    __u64 ts = bpf_ktime_get_ns();
    __u64 id = bpf_get_current_pid_tgid();
    __u32 pid = (__u32)(id >> 32);
    __u32 tid = (__u32)id;

    bpf_map_update_elem(&start_times, &pid, &ts, BPF_ANY);

    struct https_event_t *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;

    e->pid = pid;
    e->tid = tid;
    e->timestamp_ns = ts;
    e->duration_ns = 0;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    __builtin_memcpy(&e->phase, "write_enter", sizeof("write_enter"));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

// Fires on return path. We compute round-trip style elapsed time from prior write.
SEC("uretprobe/libssl.so:SSL_read")
int trace_ssl_read_return(struct pt_regs *ctx) {
    __u64 id = bpf_get_current_pid_tgid();
    __u32 pid = (__u32)(id >> 32);
    __u32 tid = (__u32)id;

    __u64 *start = bpf_map_lookup_elem(&start_times, &pid);
    if (!start) return 0;

    __u64 now = bpf_ktime_get_ns();
    __u64 duration = now - *start;
    bpf_map_delete_elem(&start_times, &pid);

    struct https_event_t *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;

    e->pid = pid;
    e->tid = tid;
    e->timestamp_ns = now;
    e->duration_ns = duration;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    __builtin_memcpy(&e->phase, "read_return", sizeof("read_return"));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
