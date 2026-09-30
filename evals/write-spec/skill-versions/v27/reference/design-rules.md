# Design rules

Apply these when you build or correct the inventory (steps 4–7). Each one came from an eval failure.

## Reuse
- Reuse existing components. A component that provides part of what is needed is reused (through an extra input, a wrapper, or a call) unless you state why that cannot work.
- Change an existing component in place instead of adding a parallel one. Add a parallel one only when a named reader needs the old meaning.
- Share picklist values through a global value set instead of copying them, unless that would restrict values other writers set; then list it as a proposal.
- Do not widen broad permission sets. Prefer a new, dedicated permission set.

## Mechanism
- Prefer the platform's standard mechanism for the job (assignment rules, roll-ups, validation rules), then flows, then code. When you choose a less standard option, give the evidence in Section 3.
- Do not add code only to make something testable. When code is needed anyway, keep the related logic for the same object and event in that component; do not split it across a flow and a trigger.
- Automation fires on the events the requirement names. Missing targets or data do not block the user's main transaction unless the requirement demands it.
- Cover records that start or stop matching the criteria on update, so the requirement's rule stays true. Do not add behavior in the opposite direction unless correctness needs it.

## Scope
- Every change traces to the requirement and serves a user, caller, or responsibility.
- Drop, or list in Section 8 as proposals: behavior nobody asked for, speculative components (for example a permission set nobody needs), and scope filters the requirement does not state.
- Already met: say so. Mostly met: the inventory covers only the verified gap, with no nearby enhancements. A defect in an existing component that the requirement does not depend on (for example an edge case) is a proposal, not a change.
- Existing data that breaks a new rule: enforce the rule on create and on change, and list the clean-up as a data step. Whether a value is required follows the data shape unless the requirement says otherwise.
- Respect email opt-out and privacy settings by default; that is not a question.
- Derived values are filled when blank; they do not overwrite existing values, unless the requirement asks for that.

## Special cases
- When the requirement fixes a weakness or cleans up a set of components, check every object for siblings with the same pattern or origin (same kind of action, same naming or ID block). Cover them or list them in Section 8.
- Changing a shared UI component (list view, layout, page) changes it for everyone. Say so, and prefer adding a new one when the change would mislead or remove access.
- A security fix must not be bypassable by the same actor (for example through a caller-supplied ID used for authorization). If it can be bypassed, that is blocking.

## Access
- Read access verbs in their business sense: "manage" means create, read, edit, and delete; "create" includes editing what was created.
- Include access that a delivered responsibility needs in order to work (for example Read on a lookup target, or a grant for an integration user that needs it).
- A grant that no responsibility needs, to an integration, connector, or broad permission set, is an open decision.
- For a new field, name the exact permission sets and profiles that get access and those that do not.
