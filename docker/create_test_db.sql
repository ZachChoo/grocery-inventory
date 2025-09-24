/*
- Ensure that the test database exists for automated tests.
- Drop the test database if it already exists to guarantee a clean slate for each test run.
*/
DROP DATABASE IF EXISTS grocery_inventory_test;
CREATE DATABASE grocery_inventory_test;