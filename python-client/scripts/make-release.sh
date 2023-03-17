set -e

DIR="$(dirname $(readlink -f $0))"

die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 1 ] || die "1 argument required, $# provided"
echo $1 | grep -E -q '^[0-9]+\.[0-9]+\.[0-9]+([ab]\d+)?$' ||
  die "Version should match '^[0-9]+\.[0-9]+\.[0-9]+([ab]\d+)?$', $1 provided"

if [ -n "$1" ]; then
  git stash || true
  git pull
  pyprojpath="$DIR/../pyproject.toml"
  echo "Setting version to $1 in $pyprojpath"
  sed -i '' "s/^version = \".*$/version = \"$1\"/" "$pyprojpath"
  git add "$pyprojpath"
  git commit -m "Version $1"
  git tag -a "python-client-v$1" -m "v$1"
  git push
  git push origin "python-client-$1"
else
  echo "New version is not specified"
fi
