# @version ^0.3.10

"""
TaxFilingGuard

Minimal emergency guard companion for TaxFilingSafeModule deployments. Safe
operators can use this contract as a policy anchor for incident response: the
owner can pause guarded module activity and maintain the same allowlist of module
execution targets expected by the module.

Production Safe guard integrations should implement the full Safe Guard interface
for the specific Safe version in use and should be audited with the module.
"""

owner: public(address)
paused: public(bool)
allowed_execution_target: public(HashMap[address, bool])


event GuardPaused:
    by: address


event GuardUnpaused:
    by: address


event GuardExecutionTargetUpdated:
    target: indexed(address)
    allowed: bool


@external
def __init__():
    self.owner = msg.sender


@internal
def _only_owner():
    assert msg.sender == self.owner, "owner only"


@external
def set_execution_target_allowed(target: address, allowed: bool):
    self._only_owner()
    assert target != empty(address), "target required"
    self.allowed_execution_target[target] = allowed
    log GuardExecutionTargetUpdated(target, allowed)


@external
def pause_guard():
    self._only_owner()
    self.paused = True
    log GuardPaused(msg.sender)


@external
def unpause_guard():
    self._only_owner()
    self.paused = False
    log GuardUnpaused(msg.sender)


@external
@view
def can_execute_module_target(target: address) -> bool:
    return not self.paused and self.allowed_execution_target[target]
