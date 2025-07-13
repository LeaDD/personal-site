# personal-site

## ⚠️ SQLite + Render Deployment Notes

- This app uses SQLite with a persistent disk on Render.
- The database file is mounted at `/data/posts.db` via Render Disk.

### 💡 Local vs Production

- Locally: SQLite DB is created at `instance/posts.db`.
- On Render: SQLite DB path is set using the `DB_URI` environment variable:

DB_URI=sqlite:////data/posts.db

### 🛑 Important Deployment Rules

- Never commit `posts.db` to the repo.
- Never call `db.create_all()` or run `init_db.py` in production.
- To update schema:
- Run `flask db migrate` + `flask db upgrade` locally
- Commit and push
- Then run `flask db upgrade` on Render shell after deploy

### ✅ Render Setup Checklist

- Add Render Disk (`/data`) to persist the database
- Set `DB_URI` to `sqlite:////data/posts.db` in environment variables
