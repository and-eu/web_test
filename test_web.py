import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import *


@pytest.fixture(scope="class")
def driver_init(request):
    options = Options()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Edge(options=options)
    request.cls.driver = driver
    driver.get("https://www.saucedemo.com/")
    driver.implicitly_wait(2)
    yield driver
    driver.close()


@pytest.mark.usefixtures("driver_init")
class BasicTest:
    driver: webdriver.Edge

    def login(self, username, password):
        # Helper method to log in
        self.driver.find_element(By.ID, "user-name").clear()
        self.driver.find_element(By.ID, "user-name").send_keys(username)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()


class TestLogin(BasicTest):

    def setup_method(self):
        self.driver.get("https://www.saucedemo.com/")

    def teardown_method(self):
        self.driver.delete_all_cookies()

    @pytest.mark.parametrize("username,password", [
        ("", ""),
        ("standard_user", ""),
        ("", "secret_sauce"),
        ("wrong_user", "secret_sauce"),
        ("standard_user", "wrong_pass")
    ], ids=[
        "Empty username and password",
        "Valid username empty password",
        "Empty username valid password",
        "Wrong username valid password",
        "Valid username wrong password"
    ])
    def test_failed_login(self, username, password):
        self.login(username, password)
        error_message = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'error-message-container')))
        assert "Epic sadface" in error_message.text

    @pytest.mark.parametrize("username,password", [
        ("standard_user", "secret_sauce")
    ], ids=[
        "Standard user with valid password",
    ])
    def test_successful_login(self, username, password):
        self.login(username, password)
        success = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'inventory_container')))
        assert success


class TestProductNavigation(BasicTest):

    def setup_method(self):
        self.driver.get("https://www.saucedemo.com/")
        self.login("standard_user", "secret_sauce")
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'inventory_container')))

    def test_navigate_to_prod_detail(self, index=0):
        items = self.driver.find_elements(By.CLASS_NAME, "inventory_item_name")
        items[index].click()
        item = (WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'inventory_details_container'))))
        assert item

    def test_navigate_back_from_prod_detail(self):
        self.test_navigate_to_prod_detail()
        self.driver.find_element(By.ID, "back-to-products").click()
        main = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'inventory_container')))
        assert main

    def test_all_items_button(self):
        self.test_navigate_to_prod_detail(1)
        self.driver.find_element(By.ID, "react-burger-menu-btn").click()
        self.driver.find_element(By.ID, "inventory_sidebar_link").click()
        main = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'inventory_container')))
        assert main

    def test_navigate_to_cart(self):
        self.driver.find_element(By.ID, "shopping_cart_container").click()
        title = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'title')))
        assert 'Your Cart' in title.text

    def test_navigate_back_from_cart(self):
        self.test_navigate_to_cart()
        self.driver.find_element(By.ID, "continue-shopping").click()
        main = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'inventory_container')))
        assert main

    def test_add_and_remove_product_from_cart(self):
        self.driver.find_element(By.ID, "add-to-cart-sauce-labs-bike-light").click()
        cart_badge = self.driver.find_element(By.CLASS_NAME, "shopping_cart_badge")
        assert int(cart_badge.text) == 1

        self.driver.find_element(By.ID, "remove-sauce-labs-bike-light").click()
        with pytest.raises(NoSuchElementException) as excinfo:
            self.driver.find_element(By.CLASS_NAME, "shopping_cart_badge")
        assert 'Unable to locate element' in excinfo.value.msg

    def test_add_and_remove_product_from_cart_detail(self):
        self.test_navigate_to_prod_detail(2)
        self.driver.find_element(By.ID, "add-to-cart").click()
        item_name = self.driver.find_element(By.CSS_SELECTOR, "div[data-test='inventory-item-name']").text
        self.test_navigate_to_cart()
        item_cart = self.driver.find_element(By.CLASS_NAME, "inventory_item_name").text
        assert item_name == item_cart

        self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn_secondary.btn_small.cart_button").click()
        with pytest.raises(NoSuchElementException) as excinfo:
            self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn_secondary.btn_small.cart_button")
        assert 'Unable to locate element' in excinfo.value.msg


class TestCheckout(BasicTest):
    def setup_method(self):
        try:
            self.driver.get("https://www.saucedemo.com/")
            self.login("standard_user", "secret_sauce")
            self.driver.find_element(By.ID, "add-to-cart-sauce-labs-backpack").click()
            self.driver.find_element(By.ID, "add-to-cart-sauce-labs-bolt-t-shirt").click()
            self.driver.find_element(By.ID, "shopping_cart_container").click()
            title = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'title')))
            assert 'Your Cart' in title.text, "Cart can't load"
            items = [el.text for el in self.driver.find_elements(By.CLASS_NAME, "inventory_item_name")]
            assert "Sauce Labs Backpack" in items, "Item not in cart"
            assert "Sauce Labs Bolt T-Shirt" in items, "Item not in cart"
        except Exception as e:
            pytest.fail(f"Setup failed: {str(e)}", pytrace=True)

    def test_checkout_process(self):
        self.driver.find_element(By.ID, "checkout").click()
        title = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'title')))
        assert 'Checkout' in title.text, "Checkout fail"

        self.driver.find_element(By.ID, "first-name").send_keys("Test")
        self.driver.find_element(By.ID, "last-name").send_keys("User")
        self.driver.find_element(By.ID, "postal-code").send_keys("12345")
        self.driver.find_element(By.ID, "continue").click()
        title = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'title')))
        assert 'Overview' in title.text, "Information page continue fail"

        items = [el.text for el in self.driver.find_elements(By.CLASS_NAME, "inventory_item_name")]
        assert "Sauce Labs Backpack" in items, "First item not in overview page"
        assert "Sauce Labs Bolt T-Shirt" in items, "Second item not in overview page"

        prices = [el.text for el in self.driver.find_elements(By.CLASS_NAME, "inventory_item_price")]
        calulated_subtotal = float(prices[0][1:])+float(prices[1][1:])
        subtotal = float(self.driver.find_element(By.CLASS_NAME, "summary_subtotal_label").text[-5:])
        assert calulated_subtotal == subtotal
        total = float(self.driver.find_element(By.CLASS_NAME, "summary_total_label").text[-5:])
        assert round(calulated_subtotal*1.08, 2) == total

        self.driver.find_element(By.ID, "finish").click()
        confirmation_msg = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'complete-header')))
        assert "Thank you for your order!" in confirmation_msg.text

