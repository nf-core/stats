// Verify every source query in sources/ produced output.
//
// `evidence sources` exits 0 even when an individual query fails (it logs the
// error and moves on), so CI cannot rely on the exit code. A query that built
// successfully gets a directory under .evidence/meta/<source>/<query>/; a query
// that errored gets none. Compare the two sets to surface failures.
import { readdirSync, existsSync } from 'node:fs';

const SOURCES_DIR = 'sources';
const META_DIR = '.evidence/meta';

const dirsIn = (path) =>
	readdirSync(path, { withFileTypes: true })
		.filter((entry) => entry.isDirectory())
		.map((entry) => entry.name);

if (!existsSync(META_DIR)) {
	console.error(`${META_DIR} missing - did \`npm run sources\` run?`);
	process.exit(1);
}

let failed = false;

for (const source of dirsIn(SOURCES_DIR)) {
	const queries = readdirSync(`${SOURCES_DIR}/${source}`)
		.filter((file) => file.endsWith('.sql'))
		.map((file) => file.replace(/\.sql$/, ''));

	const metaPath = `${META_DIR}/${source}`;
	const built = existsSync(metaPath) ? dirsIn(metaPath) : [];
	const missing = queries.filter((query) => !built.includes(query));

	if (missing.length) {
		failed = true;
		console.error(`${source}: ${missing.length} query(s) produced no output:`);
		for (const query of missing) console.error(`  - ${source}/${query}.sql`);
	} else {
		console.log(`${source}: all ${queries.length} queries built`);
	}
}

if (failed) {
	console.error('\nA source query failed. Scroll up to the `npm run sources` output');
	console.error('for the database error. A common cause is SQL referencing a column');
	console.error('the ingestion pipeline has not created yet - run the pipeline first.');
	process.exit(1);
}
