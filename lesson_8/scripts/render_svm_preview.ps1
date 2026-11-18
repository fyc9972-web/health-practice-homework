param([int]$Width = 1300, [string]$ReportSubdir = 'svm-report-preview')
$ErrorActionPreference = 'Stop'
$lessonRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$reportRoot = Join-Path (Join-Path $lessonRoot 'results') $ReportSubdir
$pdfPath = (Get-ChildItem -LiteralPath $reportRoot -Filter '*.pdf' | Select-Object -First 1).FullName
if (-not $pdfPath) { throw 'Export the report PDF before rendering.' }
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime] | Out-Null
$script:operationMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and
    $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1
$script:actionMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and
    $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
} | Select-Object -First 1
function Wait-Operation($operation, [Type]$resultType) {
    $task = $script:operationMethod.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait()
    return $task.Result
}
function Wait-Action($operation) {
    $task = $script:actionMethod.Invoke($null, @($operation))
    $task.Wait()
}
$file = Wait-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfPath)) ([Windows.Storage.StorageFile])
$pdf = Wait-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$renderRoot = Join-Path $reportRoot 'preview'
New-Item -ItemType Directory -Force -Path $renderRoot | Out-Null
Write-Output ('Page count: ' + $pdf.PageCount)
for ($index = 0; $index -lt $pdf.PageCount; $index++) {
    $page = $pdf.GetPage($index)
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $options = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $options.DestinationWidth = $Width
    Wait-Action ($page.RenderToStreamAsync($stream, $options))
    $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
    $loaded = Wait-Operation ($reader.LoadAsync([uint32]$stream.Size)) ([uint32])
    $bytes = New-Object byte[] ([int]$stream.Size)
    $reader.ReadBytes($bytes)
    $imagePath = Join-Path $renderRoot ('page-{0:D2}.png' -f ($index + 1))
    [System.IO.File]::WriteAllBytes($imagePath, $bytes)
    $reader.Dispose(); $stream.Dispose(); $page.Dispose()
    Write-Output $imagePath
}
exit 0
