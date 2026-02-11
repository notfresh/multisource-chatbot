zask() {
  local dir="/c/projects/multi-llm"
  cd "$dir" || return 1
  source venv/Scripts/activate
  python manage_core.py "$@"
}