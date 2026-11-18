param([string]$ReportSubdir = 'svm-report')
$ErrorActionPreference='Stop'
$lessonRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$reportRoot=Join-Path (Join-Path $lessonRoot 'results') $ReportSubdir
$inputPath=(Get-ChildItem -LiteralPath $reportRoot -Filter '*.docx' | Select-Object -First 1).FullName
if(-not $inputPath){throw 'Report DOCX was not generated.'}
$outputPath=[System.IO.Path]::ChangeExtension($inputPath,'.pdf')
$word=New-Object -ComObject Word.Application
$word.Visible=$false;$word.DisplayAlerts=0
try {
    $document=$word.Documents.Open($inputPath,$false,$true,$false)
    $document.Repaginate()
    $document.ExportAsFixedFormat($outputPath,17)
    $audit=Join-Path $reportRoot 'analysis\word-text-by-page.json'
    $count=$document.Range().Information(4)
    $pageRecords=@()
    for($n=1;$n -le $count;$n++){
        $start=$document.GoTo(1,1,$n).Start
        if($n -lt $count){$end=$document.GoTo(1,1,($n+1)).Start}else{$end=$document.Content.End}
        $text=$document.Range($start,$end).Text
        $pageRecords+=@{page=$n;characters=$text.Length;text=$text}
    }
    $pageRecords | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $audit -Encoding UTF8
    $document.Close(0)
    Write-Output $outputPath
    Write-Output ('Word page records: '+$count)
} finally {$word.Quit()}
