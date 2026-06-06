# FitStack API smoke test — runs against production
$BaseUrl = "https://rajatjoshi.fit"
$Timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$Email = "test_$Timestamp@test.com"
$Password = "Test1234!"
$Headers = @{ "Content-Type" = "application/json" }

$script:Passed = 0
$script:Failed = 0
$script:Token = $null
$script:WorkoutId = $null
$script:ExerciseId = $null

function Write-StepResult {
    param(
        [int]$Step,
        [string]$Name,
        [bool]$Success,
        [object]$Data = $null,
        [string]$Error = $null
    )

    if ($Success) {
        $script:Passed++
        Write-Host "Step $Step PASS - $Name" -ForegroundColor Green
    } else {
        $script:Failed++
        Write-Host "Step $Step FAIL - $Name" -ForegroundColor Red
        if ($Error) {
            Write-Host "  Error: $Error" -ForegroundColor Red
        }
    }

    if ($null -ne $Data) {
        Write-Host "  Response:" -ForegroundColor DarkGray
        Write-Host ($Data | ConvertTo-Json -Depth 6) -ForegroundColor Gray
    }
    Write-Host ""
}

function Invoke-Api {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null,
        [hashtable]$ExtraHeaders = @{}
    )

    $params = @{
        Uri         = "$BaseUrl$Path"
        Method      = $Method
        Headers     = ($Headers.Clone())
        ContentType = "application/json"
    }

    foreach ($key in $ExtraHeaders.Keys) {
        $params.Headers[$key] = $ExtraHeaders[$key]
    }

    if ($null -ne $Body) {
        $params.Body = ($Body | ConvertTo-Json -Compress)
    }

    return Invoke-RestMethod @params
}

Write-Host "FitStack Smoke Test" -ForegroundColor Cyan
Write-Host "Target: $BaseUrl"
Write-Host "Email:  $Email"
Write-Host ""

# Step 1 — Register
try {
    $registerResponse = Invoke-Api -Method Post -Path "/auth/register" -Body @{
        email    = $Email
        password = $Password
        name     = "Smoke Test User"
    }
    $registerOk = ($registerResponse.email -eq $Email)
    Write-StepResult -Step 1 -Name "Register user" -Success $registerOk -Data $registerResponse
} catch {
    Write-StepResult -Step 1 -Name "Register user" -Success $false -Error $_.Exception.Message
}

# Step 2 — Login
try {
    $loginResponse = Invoke-Api -Method Post -Path "/auth/login" -Body @{
        email    = $Email
        password = $Password
    }
    $script:Token = $loginResponse.access_token
    $loginOk = [bool]$script:Token
    Write-StepResult -Step 2 -Name "Login and capture JWT" -Success $loginOk -Data @{
        access_token = if ($script:Token) { "$($script:Token.Substring(0, [Math]::Min(20, $script:Token.Length)))..." } else { $null }
        token_type   = $loginResponse.token_type
    }
} catch {
    Write-StepResult -Step 2 -Name "Login and capture JWT" -Success $false -Error $_.Exception.Message
}

$authHeaders = @{ Authorization = "Bearer $script:Token" }

# Step 3 — Create workout
try {
    if (-not $script:Token) { throw "No JWT token from login step" }

    $workoutResponse = Invoke-Api -Method Post -Path "/workouts" -Body @{
        name         = "Push Day"
        workout_type = "strength"
    } -ExtraHeaders $authHeaders

    $script:WorkoutId = $workoutResponse.id
    $workoutOk = ($workoutResponse.name -eq "Push Day") -and ($workoutResponse.workout_type -eq "strength")
    Write-StepResult -Step 3 -Name "Create workout 'Push Day'" -Success $workoutOk -Data $workoutResponse
} catch {
    Write-StepResult -Step 3 -Name "Create workout 'Push Day'" -Success $false -Error $_.Exception.Message
}

# Step 4 — Fetch exercises and grab first ID
try {
    $exercisesResponse = Invoke-Api -Method Get -Path "/exercises"

    if ($exercisesResponse.Count -eq 0) {
        throw "Exercises list is empty - seed exercises first via POST /exercises"
    }

    $script:ExerciseId = $exercisesResponse[0].id
    $exercisesOk = [bool]$script:ExerciseId
    Write-StepResult -Step 4 -Name "Fetch exercises and grab first ID" -Success $exercisesOk -Data @{
        count          = $exercisesResponse.Count
        first_exercise = $exercisesResponse[0]
    }
} catch {
    Write-StepResult -Step 4 -Name "Fetch exercises and grab first ID" -Success $false -Error $_.Exception.Message
}

# Step 5 — Log a set
try {
    if (-not $script:WorkoutId) { throw "No workout ID from create step" }
    if (-not $script:ExerciseId) { throw "No exercise ID from exercises step" }
    if (-not $script:Token) { throw "No JWT token from login step" }

    $logResponse = Invoke-Api -Method Post -Path "/workouts/$($script:WorkoutId)/log" -Body @{
        exercise_id = $script:ExerciseId
        sets        = 4
        reps        = 8
        weight_kg   = 100
    } -ExtraHeaders $authHeaders

    $logOk = ($logResponse.sets -eq 4) -and ($logResponse.reps -eq 8) -and ($logResponse.weight_kg -eq 100)
    Write-StepResult -Step 5 -Name "Log set (4x8 @ 100kg)" -Success $logOk -Data $logResponse
} catch {
    Write-StepResult -Step 5 -Name "Log set (4x8 @ 100kg)" -Success $false -Error $_.Exception.Message
}

# Step 6 — Fetch workout logs and verify set appears
try {
    if (-not $script:WorkoutId) { throw "No workout ID from create step" }
    if (-not $script:Token) { throw "No JWT token from login step" }

    $logsResponse = Invoke-Api -Method Get -Path "/workouts/$($script:WorkoutId)/logs" -ExtraHeaders $authHeaders

    $matchingLog = $logsResponse | Where-Object {
        $_.exercise_id -eq $script:ExerciseId -and
        $_.sets -eq 4 -and
        $_.reps -eq 8 -and
        $_.weight_kg -eq 100
    } | Select-Object -First 1

    $logsOk = ($null -ne $matchingLog) -and ($logsResponse.Count -ge 1)
    Write-StepResult -Step 6 -Name "Fetch workout logs and verify set" -Success $logsOk -Data @{
        total_logs  = $logsResponse.Count
        matching_log = $matchingLog
        all_logs    = $logsResponse
    }
} catch {
    Write-StepResult -Step 6 -Name "Fetch workout logs and verify set" -Success $false -Error $_.Exception.Message
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Results: $script:Passed passed, $script:Failed failed" -ForegroundColor $(if ($script:Failed -eq 0) { "Green" } else { "Red" })

if ($script:Failed -eq 0) {
    Write-Host "OVERALL: PASS" -ForegroundColor Green
    exit 0
} else {
    Write-Host "OVERALL: FAIL" -ForegroundColor Red
    exit 1
}
