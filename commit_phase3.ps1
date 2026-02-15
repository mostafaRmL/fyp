# Phase 3 commit script
cd "C:\Users\MostafaRamma_4uiuncw\OneDrive - SirenAssociates\Desktop\fyp"

Write-Host "Adding Phase 3 files..."
git add app\services\similarity_medicine_service.py
git add test_phase3_sanity.py
git add test_phase3_quick.py
git add test_phase3_offline.py

Write-Host "Committing..."
git commit -m "Phase 3: Orchestration service - search_by_symptom, search_by_disease, drug similarity"

Write-Host "Pushing to GitHub..."
git push origin v2.0-similarity

Write-Host "Done!"
