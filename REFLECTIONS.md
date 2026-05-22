# REFLECTIONS

## 1. Multi-account
To run `costctl` against 100 AWS accounts, I would not run it manually one account at a time. I would use cross-account IAM roles so one main account can assume a role into each target account. Then I would loop through the accounts, run the same command in each one, and collect the results into one combined CSV report with the account ID included. That would make the tool more scalable and easier to review.

## 2. `idle` vs Trusted Advisor
I would trust `idle` more when I want a quick and recent view of usage, for example if I need to check whether an EC2 instance was mostly inactive in the last 24 hours. I would trust Trusted Advisor more for bigger decisions because its 14-day window gives a more stable picture and reduces the chance of deleting something that was only quiet for one day. In short, `idle` is better for fast signals, while Trusted Advisor is better for safer long-term decisions.

## 3. `clean --apply` blast radius
If I accidentally ran `clean --tag Environment=dev --apply` in a shared account, I would want several safety controls in place. First, I would want dry-run by default with a very clear summary of which resources will be deleted. Second, I would want an extra confirmation step for bulk deletion, such as typing the exact account ID or the tag value before the command continues. Third, I would want tighter IAM permissions, account separation, and backup or recovery options so one mistake cannot damage another team’s resources too much. These controls would reduce the blast radius a lot.

## 4. AI assistance
Almost all of the code in this repository came from AI tools. My role was mainly to provide the outline, explain the intended direction, and give the key insights or decisions that the implementation should follow. After that, the AI tools generated the actual code, and I reviewed the results to decide what should be kept, adjusted, or regenerated.

The same pattern applied to the written reflection work. I created the outline and provided the key ideas and personal insights first, then used AI to expand those points into full answers, paraphrase them, and improve grammar and clarity. So the final wording was AI-assisted, but the structure and core content still came from my own thinking.

## 5. W7 carry-over
For W7, I would keep `list`, `cost`, `tag`, and `idle`, and I would keep `migrate-gp3` at least in dry-run mode. These commands fit a production-style multi-account setup because they focus on visibility, governance, and cost optimization instead of destructive action. `list` helps build inventory across accounts, `cost` supports chargeback and tag-based cost analysis, `tag` helps enforce the tagging strategy that our evidence pack depends on, `idle` helps detect underused EC2 instances, and `migrate-gp3` can identify storage savings opportunities before any change is applied.

I would drop or heavily restrict `terminate` and `clean --apply` in W7 because they create too much blast radius in shared or production accounts. In a multi-account environment, one wrong filter or one mistaken account target could delete live resources for another team. If those commands are kept at all, they should be limited behind stronger approval steps, account allowlists, and dry-run-first workflows. This matches the direction of our W6 evidence, where we focused more on safe guardrails, tagging discipline, scheduled automation, and controlled remediation than on manual destructive operations.
