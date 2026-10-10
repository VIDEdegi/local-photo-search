param([switch]$ProtectMain)
# Uses an existing VIDEdegi Git credential in memory. Never prints/stores tokens.
# Does not change visibility, push code, or publish a release.
$ErrorActionPreference='Stop'
$env:GIT_TERMINAL_PROMPT='0'
$env:GCM_INTERACTIVE='Never'
$saved="protocol=https`nhost=github.com`nusername=VIDEdegi`n`n" | git -c credential.interactive=never credential fill
if($LASTEXITCODE -ne 0){throw 'GitHub authentication required'}
$pairs=@{}
foreach($line in $saved){$s=$line.Split('=',2);if($s.Count -eq 2){$pairs[$s[0]]=$s[1]}}
$headers=@{Authorization="Bearer $($pairs.password)";Accept='application/vnd.github+json';'X-GitHub-Api-Version'='2022-11-28'}
$saved=$null;$pairs=$null
function Api($method,$path,$body=$null){
  $args=@{Method=$method;Uri="https://api.github.com/$path";Headers=$headers}
  if($null -ne $body){$args.Body=($body | ConvertTo-Json -Depth 15 -Compress);$args.ContentType='application/json; charset=utf-8'}
  Invoke-RestMethod @args
}
try {
  if((Api GET 'user').login -ne 'VIDEdegi'){throw 'Wrong GitHub account'}
  $name='repos/VIDEdegi/local-photo-search'
  try{$repo=Api GET $name}catch{
    if([int]$_.Exception.Response.StatusCode -ne 404){throw}
    $repo=Api POST 'user/repos' @{name='local-photo-search';private=$true;auto_init=$false;has_issues=$true;has_projects=$false;has_wiki=$false;description='Windows向けの無料ローカルAI写真検索アプリ';homepage='https://videdegi.com';allow_auto_merge=$false}
  }
  if(!$repo.private){throw 'Repository is already public; inspect before changing settings'}
  $repo=Api PATCH $name @{has_issues=$true;has_projects=$false;has_wiki=$false;has_discussions=$false;allow_auto_merge=$false;homepage='https://videdegi.com';description='Windows向けの無料ローカルAI写真検索アプリ'}
  $null=Api PUT "$name/topics" @{names=@('windows','tauri','photo-search','local-ai','embeddinggemma')}
  $null=Api PUT "$name/actions/permissions/workflow" @{default_workflow_permissions='read';can_approve_pull_request_reviews=$false}
  $results=[ordered]@{repository=$repo.html_url;private=$repo.private;issues=$repo.has_issues;wiki=$repo.has_wiki;projects=$repo.has_projects;discussions=$repo.has_discussions;auto_merge=$repo.allow_auto_merge;actions_default='read'}
  foreach($path in @('vulnerability-alerts','private-vulnerability-reporting')){
    try{$null=Api PUT "$name/$path";$results[$path]='enabled'}catch{$results[$path]="Not applied (HTTP $([int]$_.Exception.Response.StatusCode)); check after Public approval"}
  }
  if($ProtectMain){
    $rules=@{name='main safety';target='branch';enforcement='active';bypass_actors=@();conditions=@{ref_name=@{include=@('refs/heads/main');exclude=@()}};rules=@(@{type='deletion'},@{type='non_fast_forward'},@{type='pull_request';parameters=@{required_approving_review_count=0;dismiss_stale_reviews_on_push=$false;require_code_owner_review=$false;require_last_push_approval=$false;required_review_thread_resolution=$true}},@{type='required_status_checks';parameters=@{required_status_checks=@(@{context='basic'});strict_required_status_checks_policy=$true;do_not_enforce_on_create=$true}})}
    try{$rule=Api POST "$name/rulesets" $rules;$results.ruleset=$rule.id}catch{$results.ruleset="Not applied (HTTP $([int]$_.Exception.Response.StatusCode)); apply after Public approval"}
  }
  $out=Join-Path (Split-Path $PSScriptRoot -Parent) 'data/release-tests/publication/github-settings.json'
  New-Item -ItemType Directory -Force (Split-Path $out -Parent) | Out-Null
  $results | ConvertTo-Json | Set-Content $out -Encoding utf8
  $results | ConvertTo-Json
}finally{$headers=$null}
