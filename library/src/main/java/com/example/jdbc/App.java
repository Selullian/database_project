package com.example.jdbc;

import java.sql.*;

public class App {
  public static void main(String[] args) {
    // H2 in-memory database URL; DB_CLOSE_DELAY=-1 keeps data until JVM exits
    String url = "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1";
    try (Connection conn = DriverManager.getConnection(url, "sa", "")) {
      try (Statement st = conn.createStatement()) {
        st.execute("CREATE TABLE users (id BIGINT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100))");
      }

      // Insert a row
      try (PreparedStatement ps = conn.prepareStatement("INSERT INTO users(id, name, email) VALUES(?, ?, ?)")) {
        ps.setLong(1, 1);
        ps.setString(2, "Alice");
        ps.setString(3, "alice@example.com");
        ps.executeUpdate();
      }

      // Query all rows
      try (Statement st = conn.createStatement();
           ResultSet rs = st.executeQuery("SELECT id, name, email FROM users")) {
        System.out.println("Current users:");
        while (rs.next()) {
          System.out.println(rs.getLong("id") + "\t" + rs.getString("name") + "\t" + rs.getString("email"));
        }
      }

      // Update a row
      try (PreparedStatement ps = conn.prepareStatement("UPDATE users SET email = ? WHERE id = ?")) {
        ps.setString(1, "alice@domain.example");
        ps.setLong(2, 1);
        ps.executeUpdate();
      }

      // Delete a row
      try (PreparedStatement ps = conn.prepareStatement("DELETE FROM users WHERE id = ?")) {
        ps.setLong(1, 1);
        ps.executeUpdate();
      }

      // Check final row count
      try (Statement st = conn.createStatement();
           ResultSet rs = st.executeQuery("SELECT COUNT(*) FROM users")) {
        if (rs.next()) {
          System.out.println("Row count after delete: " + rs.getInt(1));
        }
      }
    } catch (SQLException e) {
      e.printStackTrace();
    }
  }
}
