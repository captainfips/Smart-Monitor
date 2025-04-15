current_day=$(date +'%Y-%m-%d')
backup_dir=$( dirname -- "$(readlink -f -- "$0";)";)"/"$current_day"/"
echo "Starting Backup..."
echo $backup_dir
pg_basebackup -h localhost -U postgres -D $backup_dir -F tar -z
echo "Finished."