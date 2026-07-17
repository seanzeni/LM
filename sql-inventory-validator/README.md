# SQL Inventory Validator

Standalone pipeline app for validating `ProdInventory` data before it becomes
the consolidated inventory workbook used by the coordination module.

## What It Does

1. Loads source data from SQL Server:
   - `ProdInventory.dbo.Employees`
   - `ProdInventory.dbo.Projects`
   - `ProdInventory.dbo.Elements`
   - `RSET.dbo.Efforts`
   - `RSET.dbo.Bundles`
   - `RSET.dbo.Regions`
   - `RSET.dbo.MiscEnvironmentSystem`
   - RSET Efforts are limited to active rows where `BundleExitDate IS NULL`.
2. Validates project, employee, date, and region relationships.
3. Writes customer-ready issue outputs.
4. Writes clean consolidated-inventory source rows containing only records with
   no blocking errors.
5. Writes email-ready issue groupings by responsible employee/team lead.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure

Copy the example config and update server, schema, output, and email settings:

```powershell
Copy-Item config.example.json config.json
```

The `email.domain` value is appended to four-character developer IDs from the
Employees table. For example, `ABCD` and `domain.com` become
`ABCD@domain.com`.

## Run

```powershell
python -m inventory_validator --config config.json
```

Outputs are written to the folder configured by `outputs.output_dir`.
Email actions are opt-in so hourly pipeline runs can skip them. For a weekly
draft-only review run, add `--draftemails`:

```powershell
python -m inventory_validator --config config.json --draftemails
```

`--emails` is still accepted as a backward-compatible alias for
`--draftemails`.

For a weekly SMTP send run, configure `email.from_address`, `email.smtp_host`,
`email.smtp_port`, and optional SMTP credentials in `config.json`, then use:

```powershell
python -m inventory_validator --config config.json --sendemails
```

## Test

```powershell
python -m unittest discover -s tests
```

## Date Window

The pipeline only loads projects/elements in the active implementation window:

- On days 1-14 of a month: previous month and future.
- On day 15 or later: current month and future.

This keeps old implementation data out of the validation run while still
allowing mid-month cleanup of the previous month.

## Blocking Errors

Rows with blocking errors are excluded from the consolidated inventory source
output. Warnings are reported but remain eligible.

Current blocking checks include:

- Element Project Code is missing from Projects.
- Element implementation date does not match the Project implementation date.
- Element name is longer than eight characters.
- Region validation fails for non-zero bundle TestEnvironment.

Current warnings include:

- Effort exists but the referenced Bundle is missing.
- Project Team Leader is empty.
- Element Developer is empty.
- Element Developer is not exactly four characters.
- Element Team Leader is empty.
- Project Code is longer than eight characters and is not found in RSET Efforts,
  which is flagged as `POTENTIAL_MISTYPE`.

Current info rows are not written to issue outputs. When they apply to a clean
row, they are added to the good output `Validation Notes` column:

- Project is not found in RSET Efforts yet and will be default placed.
- Bundle TestEnvironment is zero, so region mismatch errors are skipped on
  purpose while Region/System enrichment still runs.

CCID is not validated from the Projects table. Output rows derive CCID from the
first six characters of Project Code.

Rows stop further validation and assignment when:

- No matching Project exists.
- Required Element Developer is empty or not exactly four characters.
- Required Element Team Leader is empty.
- Element Imp Date does not match Project Imp Date.

Stop-condition issues are not default-placed. If RSET already has an Effort for
the project, emails may still show that existing Effort/Bundle context so users
can see what SQL currently says, but the row is not treated as assignable.

Developer IDs are not validated against Employees. Employees is used only to
resolve Team Leader last names where `Position = TL`. When a match is found,
the clean output replaces the Team Leader value with that employee's
four-character Developer ID and uses that ID for issue ownership when needed.
Project email drafts put all issue owners in `To` and resolved Team Leader
emails in `Cc`.

Email drafts are generated one file per Project Code and include separate
sections so users can tell which source owns each value:

- `RSET Data`: Associated Bundle, Bundle Sequence, Bundle dates, Effort
  TeamLead, and Effort Qual/Prod dates.
- `PID Data`: Project Imp Date, Developers, and Team Leads from the
  ProdInventory/PID-side issue ownership.
- `Issues`: grouped by owner, with one row per issue showing severity, code,
  element, type, team lead, and issue message.

When email drafts are generated, the app also writes
`email_drafts/issue_resolution_instructions.txt` with simple steps for fixing
the common issue types.

The clean CSV output is always written as `consolidated_inventory_source.csv`.
It includes:

- `Merge Region` from `MiscEnvironmentSystem.Region`.
- Associated `Bundle Id` and `Bundle Sequence`.
- Canonical `System` from MiscEnvironmentSystem.
- Canonical `Region` from MiscEnvironmentSystem.
- `Misc Lookup Source` and `Misc Lookup Detail` trace columns showing whether
  the output Region/System came from the region-prefix path, direct system
  fallback, Project Merge Region split for default TestEnvironment 0, or was
  unresolved.

MiscEnvironmentSystem is selected through the release location path:
`Effort.BundleSequence -> Bundle.Sequence -> Bundle.TestEnvironment ->
Regions.TestEnvironment -> Regions.Id prefix -> MiscEnvironmentSystem.Region
prefix`. If that cannot be resolved, the validator falls back to the
configured element source column for a direct `MiscEnvironmentSystem.System`
match. For default bundles with `TestEnvironment = 0`, the validator splits
the Project `Merge Region` value on `/`, uppercases both pieces, and uses the
first half as Region and the second half as System. If the Package contains
`ARCHIVE`, System is overridden to `PRIVATE1`.

The output workbook includes summary/detail sheets for:

- `MISSING_PROJECTS`: count of elements per missing project plus all affected
  element rows.
- `IMPLEMENTATION_DATE_MISMATCH`: count of elements per project where Element
  Imp Date does not match Project Imp Date, plus all affected element rows.
