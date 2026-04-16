CLANG ?= clang
ARCH ?= $(shell uname -m)
BPF_CFLAGS := -O2 -g -target bpf -D__TARGET_ARCH_x86
INCLUDES := -I/usr/include/$(ARCH)-linux-gnu

all: aether_https_meta_trace.bpf.o

aether_https_meta_trace.bpf.o: programs/aether_https_meta_trace.bpf.c
	$(CLANG) $(BPF_CFLAGS) $(INCLUDES) -c $< -o $@

clean:
	rm -f *.o