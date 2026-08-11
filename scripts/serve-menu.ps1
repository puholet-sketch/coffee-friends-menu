# Local preview of digital menu (board.html + JSON data)
Set-Location $PSScriptRoot\..

Write-Host "Menu: http://localhost:8080/board.html" -ForegroundColor Green
Write-Host "Ctrl+C to stop" -ForegroundColor Gray

if (Get-Command python -ErrorAction SilentlyContinue) {
  python -m http.server 8080
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  py -m http.server 8080
} else {
  Write-Host "Python not found. Install Python or open board.html via Live Server." -ForegroundColor Yellow
  Start-Process "board.html"
}
