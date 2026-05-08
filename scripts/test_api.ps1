$file = Get-Item 'uploads/Priyanshi Vaghani.pdf'
$form = @{
    file = $file
    job_title = 'UI/UX Designer'
    job_description = 'Need UI/UX design experience with Figma and React'
}
$response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/analyze/' -Method POST -Form $form
$response | Select-Object candidate_name, email, mobile, match_percentage, location | ConvertTo-Json
