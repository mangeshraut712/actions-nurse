import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Explicitly opt-in seed program for the local Actions Nurse demo dataset.
 *
 * The wrapper supplies the local administrator credentials through process
 * environment only. This class never prints credentials, query tokens, or a
 * row payload; it creates only its owned database/table and then reports
 * counts. Existing data is never replaced: an existing table must exactly
 * match the small synthetic corpus or this program aborts.
 */
public final class ZetarisDemoSeed {
    static final String DATABASE = "actions_nurse_demo_20261027_f9de7301";
    static final String TABLE = "ci_failure_signatures";
    static final String CSV_URI = "file:///home/zetaris/customer-data/shared/actions-nurse-demo/ci_failure_signatures.csv";
    static final String SYNTHETIC_SOURCE = "synthetic local Actions Nurse demo corpus";
    static final int EXPECTED_ROWS = 4;

    private ZetarisDemoSeed() {}

    public static void main(String[] args) throws Exception {
        String email = requireEnvironment("ZETARIS_LOCAL_ADMIN_EMAIL");
        String password = requireEnvironment("ZETARIS_LOCAL_ADMIN_PASSWORD");
        Class.forName("com.zetaris.lightning.jdbc.LightningDriver");

        try (Connection connection = DriverManager.getConnection(
                "jdbc:zetaris:lightning@localhost:10000", email, password);
             Statement statement = connection.createStatement()) {
            boolean databaseCreated = ensureDatabase(statement);
            if (tableExists(statement)) {
                verifyOwnedSyntheticRows(statement);
                printStatus("already_seeded");
                return;
            }
            if (!databaseCreated) {
                throw new IllegalStateException(
                        "Dedicated demo database already exists without the expected table; refusing to add data to it.");
            }

            statement.execute("CREATE LIGHTNING FILESTORE TABLE " + TABLE + " FROM " + DATABASE
                    + " FORMAT csv OPTIONS (path \"" + CSV_URI + "\", header \"true\")");
            verifyOwnedSyntheticRows(statement);
            printStatus("created");
        }
    }

    private static String requireEnvironment(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("Missing required local credential environment value: " + name);
        }
        return value;
    }

    private static boolean ensureDatabase(Statement statement) throws SQLException {
        try {
            statement.execute("CREATE LIGHTNING DATABASE " + DATABASE
                    + " DESCRIBE BY \"Synthetic Actions Nurse local demo only\" OPTIONS ()");
            return true;
        } catch (SQLException error) {
            String message = String.valueOf(error.getMessage()).toLowerCase();
            if (!message.contains("already") && !message.contains("exist")) {
                throw error;
            }
            return false;
        }
    }

    private static boolean tableExists(Statement statement) throws SQLException {
        try (ResultSet rows = statement.executeQuery("SHOW TABLES IN " + DATABASE)) {
            ResultSetMetaData metadata = rows.getMetaData();
            while (rows.next()) {
                for (int column = 1; column <= metadata.getColumnCount(); column++) {
                    String value = rows.getString(column);
                    if (value != null && (TABLE.equalsIgnoreCase(value) || value.endsWith("." + TABLE))) {
                        return true;
                    }
                }
            }
            return false;
        }
    }

    private static void verifyOwnedSyntheticRows(Statement statement) throws SQLException {
        long allRows = scalarCount(statement, "SELECT COUNT(*) AS all_rows FROM " + DATABASE + "." + TABLE);
        long markedRows = scalarCount(statement,
                "SELECT COUNT(*) AS marked_rows FROM " + DATABASE + "." + TABLE
                        + " WHERE source = '" + SYNTHETIC_SOURCE + "'");
        if (allRows != EXPECTED_ROWS || markedRows != EXPECTED_ROWS) {
            throw new IllegalStateException("Existing demo table is not the expected synthetic corpus; refusing to change it.");
        }
    }

    private static long scalarCount(Statement statement, String sql) throws SQLException {
        try (ResultSet rows = statement.executeQuery(sql)) {
            if (!rows.next()) {
                throw new IllegalStateException("Expected a count result from Zetaris.");
            }
            return rows.getLong(1);
        }
    }

    private static void printStatus(String status) {
        System.out.println("demo_seed_status=" + status
                + " database=" + DATABASE
                + " table=" + TABLE
                + " row_count=" + EXPECTED_ROWS
                + " provenance=synthetic-local-demo");
    }
}
