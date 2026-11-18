param([string]$SourcePdf,[string]$ImageDir)
$ErrorActionPreference = 'Stop'
$pdfPath=(Resolve-Path -LiteralPath $SourcePdf).Path
New-Item -ItemType Directory -Path $ImageDir -Force | Out-Null
$auditPath=(Resolve-Path -LiteralPath $ImageDir).Path
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
    $options.DestinationWidth = 2480
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
