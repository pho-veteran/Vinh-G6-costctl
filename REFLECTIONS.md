# REFLECTIONS

## 1. Multi-account
To run `costctl` against 100 AWS accounts, I would not run it manually one account at a time. I would use cross-account IAM roles so one main account can assume a role into each target account. Then I would loop through the accounts, run the same command in each one, and collect the results into one combined CSV report with the account ID included. That would make the tool more scalable and easier to review.

## 2. `idle` vs Trusted Advisor
I would trust `idle` more when I want a quick and recent view of usage, for example if I need to check whether an EC2 instance was mostly inactive in the last 24 hours. I would trust Trusted Advisor more for bigger decisions because its 14-day window gives a more stable picture and reduces the chance of deleting something that was only quiet for one day. In short, `idle` is better for fast signals, while Trusted Advisor is better for safer long-term decisions.

## 3. `clean --apply` blast radius
If I accidentally ran `clean --tag Environment=dev --apply` in a shared account, I would want several safety controls in place. First, I would want dry-run by default with a very clear summary of which resources will be deleted. Second, I would want an extra confirmation step for bulk deletion, such as typing the exact account ID or the tag value before the command continues. Third, I would want tighter IAM permissions, account separation, and backup or recovery options so one mistake cannot damage another team’s resources too much. These controls would reduce the blast radius a lot.
