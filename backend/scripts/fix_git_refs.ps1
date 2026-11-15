Set-Location i:\landlock-system\landlock
# remove the broken remote ref locally, then re-fetch cleanly
git update-ref -d refs/remotes/origin/main 2>$null
git pack-refs --all --prune
git fetch --prune origin
if ($?) {
  git branch -a
  Write-Output '--- fetch OK ---'
} else {
  Write-Output '--- fetch FAILED ---'
}
