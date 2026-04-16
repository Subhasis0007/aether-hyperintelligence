---- MODULE IncidentCommandFSM_TTrace_1776332106 ----
EXTENDS IncidentCommandFSM, Sequences, TLCExt, Toolbox, Naturals, TLC

_expression ==
    LET IncidentCommandFSM_TEExpression == INSTANCE IncidentCommandFSM_TEExpression
    IN IncidentCommandFSM_TEExpression!expression
----

_trace ==
    LET IncidentCommandFSM_TETrace == INSTANCE IncidentCommandFSM_TETrace
    IN IncidentCommandFSM_TETrace!trace
----

_inv ==
    ~(
        TLCGet("level") = Len(_TETrace)
        /\
        escalated = (TRUE)
        /\
        iteration = (0)
        /\
        state = ("POSTMORTEM")
        /\
        activeAgents = ({})
        /\
        resolved = (FALSE)
    )
----

_init ==
    /\ state = _TETrace[1].state
    /\ iteration = _TETrace[1].iteration
    /\ resolved = _TETrace[1].resolved
    /\ activeAgents = _TETrace[1].activeAgents
    /\ escalated = _TETrace[1].escalated
----

_next ==
    /\ \E i,j \in DOMAIN _TETrace:
        /\ \/ /\ j = i + 1
              /\ i = TLCGet("level")
        /\ state  = _TETrace[i].state
        /\ state' = _TETrace[j].state
        /\ iteration  = _TETrace[i].iteration
        /\ iteration' = _TETrace[j].iteration
        /\ resolved  = _TETrace[i].resolved
        /\ resolved' = _TETrace[j].resolved
        /\ activeAgents  = _TETrace[i].activeAgents
        /\ activeAgents' = _TETrace[j].activeAgents
        /\ escalated  = _TETrace[i].escalated
        /\ escalated' = _TETrace[j].escalated

\* Uncomment the ASSUME below to write the states of the error trace
\* to the given file in Json format. Note that you can pass any tuple
\* to `JsonSerialize`. For example, a sub-sequence of _TETrace.
    \* ASSUME
    \*     LET J == INSTANCE Json
    \*         IN J!JsonSerialize("IncidentCommandFSM_TTrace_1776332106.json", _TETrace)

=============================================================================

 Note that you can extract this module `IncidentCommandFSM_TEExpression`
  to a dedicated file to reuse `expression` (the module in the 
  dedicated `IncidentCommandFSM_TEExpression.tla` file takes precedence 
  over the module `IncidentCommandFSM_TEExpression` below).

---- MODULE IncidentCommandFSM_TEExpression ----
EXTENDS IncidentCommandFSM, Sequences, TLCExt, Toolbox, Naturals, TLC

expression == 
    [
        \* To hide variables of the `IncidentCommandFSM` spec from the error trace,
        \* remove the variables below.  The trace will be written in the order
        \* of the fields of this record.
        state |-> state
        ,iteration |-> iteration
        ,resolved |-> resolved
        ,activeAgents |-> activeAgents
        ,escalated |-> escalated
        
        \* Put additional constant-, state-, and action-level expressions here:
        \* ,_stateNumber |-> _TEPosition
        \* ,_stateUnchanged |-> state = state'
        
        \* Format the `state` variable as Json value.
        \* ,_stateJson |->
        \*     LET J == INSTANCE Json
        \*     IN J!ToJson(state)
        
        \* Lastly, you may build expressions over arbitrary sets of states by
        \* leveraging the _TETrace operator.  For example, this is how to
        \* count the number of times a spec variable changed up to the current
        \* state in the trace.
        \* ,_stateModCount |->
        \*     LET F[s \in DOMAIN _TETrace] ==
        \*         IF s = 1 THEN 0
        \*         ELSE IF _TETrace[s].state # _TETrace[s-1].state
        \*             THEN 1 + F[s-1] ELSE F[s-1]
        \*     IN F[_TEPosition - 1]
    ]

=============================================================================



Parsing and semantic processing can take forever if the trace below is long.
 In this case, it is advised to uncomment the module below to deserialize the
 trace from a generated binary file.

\*
\*---- MODULE IncidentCommandFSM_TETrace ----
\*EXTENDS IncidentCommandFSM, IOUtils, TLC
\*
\*trace == IODeserialize("IncidentCommandFSM_TTrace_1776332106.bin", TRUE)
\*
\*=============================================================================
\*

---- MODULE IncidentCommandFSM_TETrace ----
EXTENDS IncidentCommandFSM, TLC

trace == 
    <<
    ([escalated |-> FALSE,iteration |-> 0,state |-> "NEW",activeAgents |-> {},resolved |-> FALSE]),
    ([escalated |-> FALSE,iteration |-> 0,state |-> "TRIAGING",activeAgents |-> {},resolved |-> FALSE]),
    ([escalated |-> TRUE,iteration |-> 0,state |-> "ESCALATED",activeAgents |-> {},resolved |-> FALSE]),
    ([escalated |-> TRUE,iteration |-> 0,state |-> "POSTMORTEM",activeAgents |-> {},resolved |-> FALSE])
    >>
----


=============================================================================

---- CONFIG IncidentCommandFSM_TTrace_1776332106 ----
CONSTANTS
    Agents = { "Diag" , "Fix" , "Deploy" , "PM" , "Comms" }
    MaxIterations = 5
    MaxAgents = 15

INVARIANT
    _inv

CHECK_DEADLOCK
    \* CHECK_DEADLOCK off because of PROPERTY or INVARIANT above.
    FALSE

INIT
    _init

NEXT
    _next

CONSTANT
    _TETrace <- _trace

ALIAS
    _expression
=============================================================================
\* Generated on Thu Apr 16 15:05:08 IST 2026