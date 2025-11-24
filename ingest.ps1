$ErrorActionPreference = 'Stop'
Write-Host "Running ingestion in container..."
docker compose run --rm --entrypoint python app -m src.ingest
Write-Host "Done."