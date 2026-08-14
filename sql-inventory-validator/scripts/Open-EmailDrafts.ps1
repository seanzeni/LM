[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [string]$DraftFolder,

    [int]$MaxDrafts = 0,

    [switch]$SaveOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DraftMessage {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.FileInfo]$File
    )

    $lines = [System.IO.File]::ReadAllLines($File.FullName)
    $headers = @{}
    $bodyStart = 0

    for ($index = 0; $index -lt $lines.Count; $index++) {
        $line = $lines[$index]
        if ([string]::IsNullOrWhiteSpace($line)) {
            $bodyStart = $index + 1
            break
        }

        $separator = $line.IndexOf(":")
        if ($separator -gt 0) {
            $name = $line.Substring(0, $separator).Trim()
            $value = $line.Substring($separator + 1).Trim()
            $headers[$name] = $value
        }
    }

    $bodyLines = @()
    if ($bodyStart -lt $lines.Count) {
        $bodyLines = $lines[$bodyStart..($lines.Count - 1)]
    }

    [pscustomobject]@{
        Subject = [string]$headers["Subject"]
        To      = [string]$headers["To"]
        Cc      = [string]$headers["Cc"]
        Body    = ($bodyLines -join [Environment]::NewLine)
        Path    = $File.FullName
    }
}

$resolvedDraftFolder = Resolve-Path -LiteralPath $DraftFolder
$draftFiles = Get-ChildItem -LiteralPath $resolvedDraftFolder -Filter "*.txt" -File |
    Where-Object { $_.Name -ne "issue_resolution_instructions.txt" } |
    Sort-Object Name

if ($MaxDrafts -gt 0) {
    $draftFiles = $draftFiles | Select-Object -First $MaxDrafts
}

if (-not $draftFiles) {
    Write-Warning "No email draft .txt files found in $resolvedDraftFolder."
    return
}

$outlook = New-Object -ComObject Outlook.Application
$created = 0

foreach ($file in $draftFiles) {
    $draft = Get-DraftMessage -File $file

    if (-not $draft.To) {
        Write-Warning "Skipping '$($file.Name)' because it has no To recipients."
        continue
    }

    if ($PSCmdlet.ShouldProcess($draft.Path, "Create Outlook email draft")) {
        $mail = $outlook.CreateItem(0)
        $mail.Subject = $draft.Subject
        $mail.To = $draft.To
        $mail.CC = $draft.Cc
        $mail.Body = $draft.Body

        if ($SaveOnly) {
            $mail.Save()
        }
        else {
            $mail.Display($false)
        }

        $created++
    }
}

Write-Host "Created $created Outlook email draft(s)."
