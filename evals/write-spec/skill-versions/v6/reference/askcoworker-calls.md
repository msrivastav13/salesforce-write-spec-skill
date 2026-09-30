# AskCoworker call templates

Fill `{…}` placeholders. Each call asks one narrow question with a word limit. Broad or long requests time out; a question that fits in about 400 words returns in under a minute.

## Common header (start every call with this)

```
Specification analysis only. Do NOT make org changes, deploy, or create or modify metadata or data.
Answer only from this message and the org. Ignore earlier conversations.

Requirement: "{requirement, verbatim}"
Project: {project name}; org alias {alias}; sourceApiVersion {version}.
Established so far:
{short bullets of verified facts, user decisions, and accepted inventory, each tagged (verified by org query | user decision | reported by AskCoworker); or "nothing yet"}

Label every factual claim [Verified: <how checked>], [Proposal], or [Unknown]. Answer in full; do not resume an earlier answer.
Limit: {N} words. End with a line "Sections included: ..." and then a final line <<END-SPEC-CONTENT>>.
```

## D1 — Discovery: objects (limit 300 words)

```
Map the business concepts in the requirement onto org objects by meaning, not only by keyword (consider synonyms).
Return: title and one-sentence purpose; the objects that apply and why; their relevant fields (API name, type; formula, roll-up, and picklist details where they apply); relationships between the objects; what the requirement implies that does NOT exist.
```

## D2 — Discovery: behavior on those objects (limit 400 words)

```
Objects in scope: {list from D1}.
Return: Apex triggers and handler patterns, record-triggered flows, validation rules, scheduled or batch jobs, Apex classes, LWC, and integrations that read or write these objects; relevant permission sets and sharing; whether the requirement is already met, fully or partly, by existing features.
```

## I — Inventory (limit 500 words)

```
Propose the smallest set of metadata changes that meets the requirement. Reuse existing components first, and prefer declarative features (roll-ups, formulas, validation rules, flows) over Apex; when you choose Apex, give the reason. Do not add behavior the requirement does not ask for.
Return ONE Markdown table with exactly these columns:
| # | Action | Type | API name | Module | Group | Detail | Evidence |
- Action is Create, Update, or Delete. Type is the metadata type (for example CustomField, ApexClass, ApexTrigger, Flow, PermissionSet).
- API name is fully qualified for fields (Object__c.Field__c).
- If a change depends on an unresolved fact, begin Detail with "Conditional:" and state the condition.
- For every Delete, state the impact and prerequisites in Detail.
- One row per deployable component; list the parts a component needs to work (for example, data model objects and mappings for a data stream).
- If no metadata changes are required, write exactly "No metadata changes are required." and leave the table out.
Put alternative designs under a heading "Alternatives (not in inventory)".
```

## R — Runtime and security (limit 400 words)

```
Accepted inventory: {numbered list of Action Type API name}.
Return: runtime relationships (which events fire what, in which order, including bulk, delete, undelete, and reparenting where relevant) with evidence; execution context and sharing; CRUD/FLS; permission set changes; data exposure; and whether Data 360 (Data Cloud) is involved.
```

## T — Testing and open decisions (limit 400 words)

```
Accepted inventory: {numbered list}.
Return: the tests in the inventory mapped to behaviors; bulk, negative, and permission cases; recommended manual verification; open decisions (assumptions, unresolved choices with a recommended default, parts of the requirement not addressed), each marked blocking or non-blocking.
```

For a small inventory (eight changes or fewer), you may combine R and T into one call with a limit of 500 words.

## After a timeout

Do not resend the same request. Resend a narrower version: split the question in half, or ask only for the items still missing, and lower the word limit.
