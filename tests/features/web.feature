Feature: Web interface
    As a user
    I want to access the web application
    So that I can interact with the system

    Scenario: Visit homepage
        Given the web app is running
        When I visit "/"
        Then I should see "Hello"
