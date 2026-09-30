# Design rules

Apply these when you build or correct the inventory (steps 4–7). Each one came from an eval failure.

## Reuse
- Reuse must not change the behavior of existing components (for example restricting a field that other writers use) unless the requirement asks for it.
- Reuse existing components. A component that provides part of what is needed is reused (through an extra input, a wrapper, or a call) unless you state why that cannot work.
- Change an existing component in place instead of adding a parallel one. Add a parallel one only when a named reader needs the old meaning.
- Share picklist values through a global value set instead of copying them, unless that would restrict values other writers set; then list it as a proposal.
- Do not widen broad permission sets. Prefer a new, dedicated permission set.

## Mechanism
- Prefer the platform's standard mechanism for the job (assignment rules, roll-ups, validation rules), then flows, then code. When you choose a less standard option, give the evidence in Section 3.
- Do not add code only to make something testable. When code is needed anyway, keep the related logic for the same object and event in that component; do not split it across a flow and a trigger.
- Automation that reacts to a roll-up or formula value belongs on the parent (a record-triggered flow or trigger on the parent's update), not on the child.
- Automation fires on the events the requirement names. Missing targets or data do not block the user's main transaction unless the requirement demands it.
- Cover records that start or stop matching the criteria on update, so the requirement's rule stays true. Do not add behavior in the opposite direction unless correctness needs it.

## Scope
- A list the requirement gives (columns, fields, values) is the complete list.
- Every change traces to the requirement and serves a user, caller, or responsibility.
- Drop, or list in Section 8 as proposals: behavior nobody asked for, speculative components (for example a permission set nobody needs), and scope filters the requirement does not state.
- A design for a persona with no users today is still a normal (preventive) change.
- A component exists but is not placed or granted: the gap is only the placement or grant.
- A unique-key backfill where existing duplicates would fail keys only one record per duplicate group; the conflicts are a clean-up data step.
- Metadata exists but values are empty: the requirement is met for metadata; the population is a data step.
- Already met: say so. Mostly met: the inventory covers only the verified gap, with no nearby enhancements. A defect in an existing component that the requirement does not depend on (for example an edge case) is a proposal, not a change.
- Existing data that breaks a new rule: enforce the rule on create and on change, and list the clean-up as a data step. Whether a value is required follows the data shape unless the requirement says otherwise; if the only writer never sets it, keep it optional and list the gap.
- Respect email opt-out and privacy settings by default; that is not a question.
- Derived values are filled when blank; they do not overwrite existing values, unless the requirement asks for that.

## Special cases
- When the requirement fixes a weakness or cleans up a set of components, check every object for siblings with the same pattern or origin (same kind of action, same naming or ID block). Cover them or list them in Section 8.
- Changing a shared UI component (list view, layout, page) changes it for everyone. Say so, and prefer adding a new one when the change would mislead or remove access.
- An action or button on a shared layout or page is visible to everyone assigned to it. If some of those users lack the access the action needs, place it where only permitted users see it (a layout or page assigned to them, or visibility rules), or state who would see a failing button.
- A security fix must not be bypassable by the same actor (for example through a caller-supplied ID used for authorization). If it can be bypassed through a verified path, that is blocking; an unverifiable possible path is a risk in Section 8.

- When a change removes or breaks data that someone relies on (for example a cleared primary contact), include a notification to the record owner (for example a Task). A status change that the requirement itself asks for needs no notification; list one as a proposal.

- When the change makes existing descriptions or instructions false (agent action descriptions, help text, topic instructions), updating them is part of the inventory. Keep the still-true parts, and check the component's other descriptions too. A description-only edit to an Apex class that no test covers is a proposal, because the deploy would fail the coverage check.
- Converting an existing field to a Formula (or roll-up) type is not supported in place. Create a new field, and list the old one as a proposal to retire.

- When a user-stated sequence cannot be met literally because of a platform constraint (for example no DML before a callout), map it to the closest behavior and record the mapping as an assumption.

## Refactors
- A behavior-preserving refactor keeps signatures, sharing modes, and outputs unchanged; covers every instance the requirement names; and adds regression tests for the unchanged behavior.

## Access
- Read access verbs in their business sense: "manage" means create, read, edit, and delete; "create" includes editing what was created.
- Include access that a delivered responsibility needs in order to work (for example Read on a lookup target, or a grant for an integration user that needs it).
- A grant that no responsibility needs, to an integration, connector, or broad permission set, is an open decision.
- For a new field, name the exact permission sets and profiles that get access and those that do not. Edit access matches every place the field is editable and every stated data-entry path.
- A data step names the access the loading user or integration needs (for example temporary Edit on a new field).
- When duplicate fields are merged, the field you keep gets the access and layout placement the deleted one had, so users lose nothing. Grant profile access through Update rows, not through a broad permission set.
- When exclusive access ("only X") cannot be delivered by metadata because managed permission sets or View All/Modify All Data grants cannot be edited, it is blocking for delivery; removing those assignments in Setup is the setup step.
