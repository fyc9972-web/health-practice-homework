param(
    [Parameter(Mandatory=$true)][string]$SourceDocx,
    [Parameter(Mandatory=$true)][string]$AuditDir
)
$ErrorActionPreference = 'Stop'
$docPath = (Resolve-Path -LiteralPath $SourceDocx).Path
if (-not (Test-Path -LiteralPath $AuditDir)) { New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null }
$auditPath = (Resolve-Path -LiteralPath $AuditDir).Path
$pdfPath = Join-Path $auditPath 'word-render.pdf'
$wordApp = $null
$ownedDoc = $null
try {
    Write-Output 'WORD_STAGE=starting'
    $wordApp = New-Object -ComObject Word.Application
    $wordApp.Visible = $false
    $wordApp.DisplayAlerts = 0
    $wordApp.AutomationSecurity = 3
    $wordApp.Options.PrintBackground = $false
    Write-Output 'WORD_STAGE=opening'
    $ownedDoc = $wordApp.Documents.Open($docPath, $false, $false, $false)
    Write-Output ('WORD_CHARS=' + $ownedDoc.Content.Characters.Count)
    $ownedDoc.ActiveWindow.View.Type = 3
    Write-Output 'WORD_STAGE=repaginating'
    $ownedDoc.Repaginate()
    Write-Output 'WORD_STAGE=saving'
    $ownedDoc.Save()
    $pageCount = $ownedDoc.ComputeStatistics(2)
    Write-Output ('WORD_STAGE=exporting; pages=' + $pageCount)
    $ownedDoc.ExportAsFixedFormat($pdfPath, 17)
    $pageTexts = @()
    for ($pageIndex=1; $pageIndex -le $pageCount; $pageIndex++) {
        $startAt = $ownedDoc.GoTo(1, 1, $pageIndex).Start
        if ($pageIndex -lt $pageCount) { $endAt = $ownedDoc.GoTo(1, 1, $pageIndex+1).Start }
        else { $endAt = $ownedDoc.Content.End }
        $pageRange = $ownedDoc.Range($startAt, $endAt)
        $txt = $pageRange.Text
        $pageTexts += [pscustomobject]@{
            page = $pageIndex
            characters = $txt.Length
            start = $txt.Substring(0, [Math]::Min(120,$txt.Length))
            end = $txt.Substring([Math]::Max(0,$txt.Length-180))
        }
    }
    [pscustomobject]@{ pages=$pageCount; source=$docPath; page_texts=$pageTexts } |
        ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $auditPath 'word-layout.json') -Encoding UTF8
    Write-Output ('WORD_PAGES=' + $pageCount)
    Write-Output ('WORD_PDF=' + $pdfPath)
} finally {
    if ($null -ne $ownedDoc) {
        $ownedDoc.Close(0)
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($ownedDoc)
    }
    if ($null -ne $wordApp) {
        if ($wordApp.Documents.Count -eq 0) { $wordApp.Quit(0) }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordApp)
    }
}

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfPageRenderOptions,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.DataReader,Windows.Storage.Streams,ContentType=WindowsRuntime]

$script:asTaskOperation = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetGenericArguments().Count -eq 1 -and
    $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
$script:asTaskAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
} | Select-Object -First 1

function Await-Result($Operation, [Type]$ResultType) {
    $task = $script:asTaskOperation.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}
function Await-Action($Action) {
    $task = $script:asTaskAction.Invoke($null, @($Action))
    $task.Wait()
}

$pdfFile = Await-Result ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfPath)) ([Windows.Storage.StorageFile])
$pdf = Await-Result ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($pdfFile)) ([Windows.Data.Pdf.PdfDocument])
for ($pageIndex=0; $pageIndex -lt $pdf.PageCount; $pageIndex++) {
    $page = $pdf.GetPage([uint32]$pageIndex)
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $options = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $options.DestinationWidth = 1100
    Await-Action ($page.RenderToStreamAsync($stream,$options))
    $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
    $null = Await-Result ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
    $bytes = New-Object byte[] ([int]$stream.Size)
    $reader.ReadBytes($bytes)
    $imagePath = Join-Path $auditPath ('page-{0:D2}.png' -f ($pageIndex+1))
    [IO.File]::WriteAllBytes($imagePath,$bytes)
    $reader.Dispose()
    $stream.Dispose()
    $page.Dispose()
    Write-Output ('RENDERED=' + $imagePath)
}
