---- MODULE IncidentCommandFSM ----
EXTENDS Naturals, FiniteSets, TLC

CONSTANTS
  Agents,
  MaxIterations,
  MaxAgents

VARIABLES
  state,
  activeAgents,
  iteration,
  resolved,
  escalated

Vars == <<state, activeAgents, iteration, resolved, escalated>>

States ==
  {"NEW", "TRIAGING", "DIAGNOSING", "FIXING",
   "VERIFYING", "RESOLVED", "ESCALATED", "POSTMORTEM"}

TypeInvariant ==
  /\ state \in States
  /\ activeAgents \subseteq Agents
  /\ Cardinality(activeAgents) <= MaxAgents
  /\ iteration \in 0..MaxIterations
  /\ resolved \in BOOLEAN
  /\ escalated \in BOOLEAN

SafetyInvariant ==
  state = "FIXING" => iteration <= MaxIterations

ExclusiveTermination ==
  ~(resolved /\ escalated)

Init ==
  /\ state = "NEW"
  /\ activeAgents = {}
  /\ iteration = 0
  /\ resolved = FALSE
  /\ escalated = FALSE

Triaging ==
  /\ state = "NEW"
  /\ state' = "TRIAGING"
  /\ activeAgents' \subseteq Agents
  /\ Cardinality(activeAgents') <= MaxAgents
  /\ iteration' = iteration
  /\ resolved' = resolved
  /\ escalated' = escalated

StartDiagnosing ==
  /\ state = "TRIAGING"
  /\ state' = "DIAGNOSING"
  /\ activeAgents' \subseteq Agents
  /\ Cardinality(activeAgents') <= MaxAgents
  /\ UNCHANGED <<iteration, resolved, escalated>>

DiagnoseToFix ==
  /\ state = "DIAGNOSING"
  /\ iteration < MaxIterations
  /\ state' = "FIXING"
  /\ activeAgents' = activeAgents
  /\ iteration' = iteration + 1
  /\ resolved' = resolved
  /\ escalated' = escalated

FixToVerify ==
  /\ state = "FIXING"
  /\ state' = "VERIFYING"
  /\ activeAgents' = activeAgents
  /\ iteration' = iteration
  /\ resolved' = resolved
  /\ escalated' = escalated

VerifyResolved ==
  /\ state = "VERIFYING"
  /\ state' = "RESOLVED"
  /\ activeAgents' = {}
  /\ iteration' = iteration
  /\ resolved' = TRUE
  /\ escalated' = FALSE

VerifyRetry ==
  /\ state = "VERIFYING"
  /\ iteration < MaxIterations
  /\ state' = "DIAGNOSING"
  /\ activeAgents' = activeAgents
  /\ iteration' = iteration
  /\ resolved' = FALSE
  /\ escalated' = FALSE

Escalate ==
  /\ state \in {"TRIAGING", "DIAGNOSING", "FIXING", "VERIFYING"}
  /\ state' = "ESCALATED"
  /\ activeAgents' = {}
  /\ iteration' = iteration
  /\ resolved' = FALSE
  /\ escalated' = TRUE

PostMortemFromResolved ==
  /\ state = "RESOLVED"
  /\ state' = "POSTMORTEM"
  /\ UNCHANGED <<activeAgents, iteration, resolved, escalated>>

PostMortemFromEscalated ==
  /\ state = "ESCALATED"
  /\ state' = "POSTMORTEM"
  /\ UNCHANGED <<activeAgents, iteration, resolved, escalated>>

\* Explicit terminal self-loop so POSTMORTEM is not a deadlock
Done ==
  /\ state = "POSTMORTEM"
  /\ UNCHANGED Vars

Next ==
  \/ Triaging
  \/ StartDiagnosing
  \/ DiagnoseToFix
  \/ FixToVerify
  \/ VerifyResolved
  \/ VerifyRetry
  \/ Escalate
  \/ PostMortemFromResolved
  \/ PostMortemFromEscalated
  \/ Done

Spec ==
  Init
  /\ [][Next]_Vars
  /\ WF_Vars(Next)

Termination ==
  <>(state = "POSTMORTEM")

====
