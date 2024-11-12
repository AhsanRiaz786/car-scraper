from playwright.sync_api import sync_playwright, TimeoutError
from urllib.parse import urlparse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import requests
import time
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
from urllib.parse import urlparse
from time import sleep
from PIL import Image
from tkinter import ttk
from tkinter import messagebox


class CarScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Scraper")
        self.root.geometry("400x200")
        
        # URL Entry
        tk.Label(root, text="Enter the site URL:").pack(pady=5)
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)
        
        # Save Location
        tk.Label(root, text="Select Save Location for PDF:").pack(pady=5)
        self.save_location_button = tk.Button(root, text="Browse", command=self.select_save_location)
        self.save_location_button.pack(pady=5)
        
        self.save_path = None
        
        # Generate PDF Button
        self.generate_button = tk.Button(root, text="Generate PDF", command=self.start_pdf_generation)
        self.generate_button.pack(pady=5)
        
        # Status Label
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=5)

    def select_save_location(self):
        self.save_path = filedialog.askdirectory()
        if self.save_path:
            self.status_label.config(text=f"Save Location Selected: {self.save_path}")

    def start_pdf_generation(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a valid URL.")
            return
        if not self.save_path:
            messagebox.showerror("Error", "Please select a save location.")
            return
        
        # Check for specific sites to prompt additional data input
        if "sbtjapan" in url or "beforward" in url:
            self.show_additional_inputs(url)
        else:
            # No additional inputs needed, proceed to generate PDF
            self.generate_pdf(url, {})

    def show_additional_inputs(self, url):
        # New window for additional inputs
        additional_window = tk.Toplevel(self.root)
        additional_window.title("Additional Information")
        additional_window.geometry("400x300")
        
        # Total Price
        tk.Label(additional_window, text="Total Price").pack(pady=5)
        total_price_entry = tk.Entry(additional_window, width=20)
        total_price_entry.pack(pady=5)
        
        # Island Dropdown
        tk.Label(additional_window, text="Select Island").pack(pady=5)
        island_var = tk.StringVar()
        island_dropdown = ttk.Combobox(additional_window, textvariable=island_var)
        island_dropdown['values'] = ("Abaco", "Nassau", "Freeport", "Exuma", "Eleuthera", "Spanish Wells")
        island_dropdown.pack(pady=5)
        
        # Title Half Down Option (optional)
        tk.Label(additional_window, text="Half Down").pack(pady=5)
        title_half_down_entry = tk.Entry(additional_window, width=20)
        title_half_down_entry.pack(pady=5)
        
        # Submit Button
        submit_button = tk.Button(additional_window, text="Submit", command=lambda: self.submit_additional_inputs(
            additional_window, url, total_price_entry.get(), island_var.get(), title_half_down_entry.get()
        ))
        submit_button.pack(pady=10)

    def submit_additional_inputs(self, additional_window, url, total_price, island, title_half_down):
        additional_window.destroy()  # Close the input window

        # Collect additional data
        additional_data = {
            "Total Price": total_price+" $",
            "Island": island,
            "Half Down": title_half_down,
        }
        # Proceed to generate the PDF
        self.generate_pdf(url, additional_data)

    def generate_pdf(self, url, additional_data):
        self.status_label.config(text="Generating PDF... Please wait.")
        Thread(target=self.scrape_and_save_pdf, args=(url, additional_data)).start()

    def scrape_and_save_pdf(self, url, additional_data):
        try:
            scraper = get_scraper(url)
            scraper.scrape()

            # Add additional data to the scraper's data dictionary
            scraper.data.update(additional_data)

            scraper.car_name = scraper.car_name.replace("/", "_")  # Remove any invalid characters in filename
            filename = f"{self.save_path}/{scraper.car_name}.pdf"
            scraper.save_pdf(filename)
            self.status_label.config(text="PDF generated successfully!")
            messagebox.showinfo("Success", f"PDF generated successfully at {filename}")
        except Exception as e:
            self.status_label.config(text="Error generating PDF.")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")



class BaseScraper:
    def __init__(self, url,crop_size):
        self.crop_size = crop_size
        self.url = url
        self.data = {}
        self.images = []
        self.car_name = "Car Report"

    def scrape(self):
        """Method to be implemented by each subclass for site-specific scraping."""
        raise NotImplementedError("Subclasses must implement this method")


    def save_pdf(self, filename):
        """Generate a single-page PDF with car information and cropped images, two images per page."""
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        y_position = height - 50

        # Add logo if available
        logo_path = "lux_official_logo.png"
        try:
            logo = ImageReader(logo_path)
            logo_width, logo_height = logo.getSize()
            aspect_ratio = logo_height / logo_width
            display_width = 200
            display_height = display_width * aspect_ratio
            c.drawImage(logo, (width - display_width) / 2, y_position - display_height, 
                        width=display_width, height=display_height)
            y_position -= display_height + 40
        except Exception as e:
            print(f"Error loading logo: {e}")

        # Add Car Name as Heading
        c.setFont("Helvetica-Bold", 22)
        c.drawCentredString(width / 2, y_position, self.car_name)
        y_position -= 40

        # Split data into columns for display
        keys = list(self.data.keys())
        values = list(self.data.values())
        mid_point = len(keys) // 2
        left_keys, right_keys = keys[:mid_point], keys[mid_point:]
        left_values, right_values = values[:mid_point], values[mid_point:]

        c.setFont("Helvetica", 12)
        x_left, x_right = 10, width / 2 + 10
        y_position -= 20

        # Populate columns without extra colons
        for i in range(max(len(left_keys), len(right_keys))):
            if i < len(left_keys):
                c.drawString(x_left, y_position, f"{left_keys[i].replace(':','')}: {left_values[i]}")
            if i < len(right_keys):
                c.drawString(x_right, y_position, f"{right_keys[i].replace(':','')}: {right_values[i]}")
            y_position -= 25
            if y_position < 50:
                y_position = height - 50
                c.showPage()

        # Move to a new page for images
        c.showPage()
        y_position = height - 30  # Reset y_position for images on new page

        # Add cropped images, two per page
        for idx, img_url in enumerate(self.images):
            try:
                img_content = requests.get(img_url).content
                with io.BytesIO(img_content) as img_stream:
                    with Image.open(img_stream) as img:
                        # Crop 20 pixels from the bottom
                        img_width, img_height = img.size
                        cropped_img = img.crop((0, 0, img_width, img_height - self.crop_size))

                        # Convert cropped image to ImageReader
                        image_reader = ImageReader(cropped_img)

                        # Calculate display size with aspect ratio
                        aspect_ratio = cropped_img.height / cropped_img.width
                        img_display_width = width - 100
                        img_display_height = img_display_width * aspect_ratio

                        # Position and draw the image on the canvas
                        c.drawImage(image_reader, 50, y_position - img_display_height, 
                                    width=img_display_width, height=img_display_height)

                        # Adjust y_position for the next image or start a new page if needed
                        y_position -= img_display_height + 40
                        if idx % 2 == 1:  # After every two images, start a new page
                            c.showPage()
                            y_position = height - 40  # Reset y_position for new page

            except Exception as e:
                print(f"Failed to load or crop image {img_url}: {e}")
                continue

        c.save()

class CopartScraper(BaseScraper): 
    def __init__(self,url,crop_size):
        super().__init__(url,crop_size)
    def scrape(self):
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False,args=[
                        "--window-position=-10000,-10000",  # Position window off-screen
                        "--disable-blink-features=AutomationControlled",
                    ])
                
                page = browser.new_page()
                page.goto(self.url, wait_until="domcontentloaded", timeout=10000)
                time.sleep(10)
                # Attempt scraping the first structure
                try:
                    page.wait_for_selector("div.tab-content.f-g1.d-f", timeout=10000)
                    car_name_element = page.query_selector("h1")

                    self.car_name = car_name_element.inner_text() if car_name_element else "Car Report"

                    # Car details mapping
                    details_mapping = {
                        "Lot No": 'span[data-uname="lotdetailVinvalue"]',
                        "VIN": 'span.lot-details-desc:nth-child(1)',
                        "Title Code": 'span[data-uname="lotdetailTitledescriptionvalue"]',
                        "Odometer": 'span[data-uname="lotdetailOdometervalue"]',
                        "Retail Value": 'span[data-uname="lotdetailEstimatedretailvalue"]',
                        "Primary Damage": 'span[data-uname="lotdetailPrimarydamagevalue"]',
                        "Seconday Damage": 'span[data-uname="lotdetailSecondarydamagevalue"]',
                        "Body Style" : 'span[data-uname="lotdetailBodystylevalue"]',
                        "Cylinders": 'span[data-uname="lotdetailCylindervalue"]',
                        "Color": 'span[data-uname="lotdetailColorvalue"]',
                        "Engine Type": 'span[data-uname="lotdetailEnginetype"]',
                        "Transmission": 'span[data-uname="lotdetailTransmissionvalue"]',
                        "Drive": 'span[data-uname="lotdetailDrivevalue"]',
                        "Vehicle Type": 'span[data-uname="lotdetailvehicletype"]',
                        "Fuel": 'span[data-uname="lotdetailFuelvalue"]',
                        "Keys": 'span[data-uname="lotdetailKeyvalue"]',
                        "Seller": 'span[data-uname="lotdetailSellervalue"]',
                        "Highlights": 'span.lot-details-desc.highlights-popover-cntnt.text-CERT-D.d-flex.j-c_s-b',
                        "Sale Name" : "a[ng-click='getAllLaneSaleListResultUrl(lotDetails)']",
                        "Sale Location": "a[data-uname='lotdetailSaleinformationlocationvalue']",
                        "Sale Date": "span[data-uname='lotdetailSaleinformationsaledatevalue']",
                        "Sale Date" : "a[data-uname='lotdetailFuturelink']",
                        "Last Updated": "span[data-uname='lotdetailSaleinformationlastupdatedvalue']",
                        "Time Left" : "span[data-uname='lotdetailSaleinformationtimeleftvalue']",
                        "Current Bid" : "span.text-right.bid-price",
                        "Current Bid" : "span.bid-price"
                    }

                    # Extract data with handling for missing elements
                    for key, selector in details_mapping.items():
                        element = page.query_selector(selector)
                        if element:
                            self.data[key] = element.inner_text()

                    # Extract images
                    self.extract_images(page)
                    return
                except Exception as e:
                    print(f"First structure failed: {e}")

                # Second structure fallback
                try:
                    page.wait_for_selector("div.lot-details-section.vehicle-info", timeout=10000)
                    car_info = page.query_selector_all("div.lot-details-info")
                    self.car_name = page.query_selector("h1").inner_text()

                    current_bid_element = page.query_selector("h1.p-mt-0.amount.bidding-heading.p-d-inline-block.p-position-relative.separate-currency-symbol.ng-star-inserted")
                    if(current_bid_element):
                        self.data["Current Bid"] = current_bid_element.inner_text()

                    for div in car_info:
                        label = div.query_selector("label").inner_text()
                        value = div.query_selector("span").inner_text()
                        self.data[label] = value

                    # Handle images with pagination
                    self.extract_images_with_pagination(page)
                except Exception as e:
                    print(f"Second structure failed: {e}")
                finally:
                    browser.close()
        except TimeoutError:
            print("TimeoutError on Copart site")
        return self.data

    def extract_images(self, page):
        image_elements = page.query_selector_all("div.small-container.martop img")
        self.images = [img.get_attribute("src").replace("_thb.jpg", "_ful.jpg") for img in image_elements]

    def extract_images_with_pagination(self, page):
        for _ in range(5):
            image_elements = page.query_selector_all("div.p-galleria-thumbnail-items img")
            self.images.extend([
                img.get_attribute("src").replace("_thb.jpg", "_ful.jpg")
                for img in image_elements
            ])
            next_button = page.query_selector("span.lot-details-sprite.thumbnail-next-image-icon.p-position-absolute.p-cursor-pointer")
            if next_button:
                next_button.click()
                time.sleep(0.5)
        self.images = list(dict.fromkeys(self.images))  # Remove duplicates




class IAAIScraper(BaseScraper):
    def __init__(self,url,crop_size):
        super().__init__(url,crop_size)
    COOKIES_FILE = "cookies.json"

    def scrape(self):
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=False,args=[
                        "--window-position=-10000,-10000",  # Position window off-screen
                        "--disable-blink-features=AutomationControlled",
                    ])
                context = browser.new_context()


                # Load cookies if available

                page = context.new_page()
                
                # Load the URL without waiting for the entire network to become idle
                page.goto(self.url, wait_until="domcontentloaded", timeout=10000)
                
                try:
                    page.wait_for_selector("div.data-container", timeout=5000)
                    self.car_name = page.query_selector("h1").inner_text()

                    # Scrape data as soon as it's available
                    car_info_tables = page.query_selector_all("ul.data-list.data-list--details")
                    for table in car_info_tables:
                        rows = table.query_selector_all("li")
                        for row in rows:
                            spans = row.query_selector_all("span")
                            anchor = row.query_selector_all("a")
                            if len(spans) < 2:
                                if(len(anchor)>0 and len(spans)>0):
                                    key=spans[0].inner_text().strip()
                                    value = anchor[0].inner_text().strip()
                                    self.data[key] = value
                                    continue
                                else:
                                    continue
                            
                            key = spans[0].inner_text().strip()
                            value = spans[1].inner_text().strip()
                            self.data[key] = value
                            
                            pre_bid_status_element = page.query_selector("div.pre-bid-container")
                            auction_status_element = page.query_selector("div.pre-bid-container.mt-20")
                            if pre_bid_status_element:
                                pre_bid_status =  pre_bid_status_element.query_selector("span")
                                if pre_bid_status:
                                    self.data["Pre Bid"] = pre_bid_status.inner_text().strip()
                            if auction_status_element:
                                auction_status = auction_status_element.query_selector("p")
                                if auction_status:
                                    self.data["Auction Status"] = auction_status.inner_text().strip()
                            

                    image_elements = page.query_selector_all("img")
                    for img in image_elements:
                        if(img.get_attribute('src') is not None and img.get_attribute('src')[0:21]=="https://vis.iaai.com/"):
                            self.images.append(img.get_attribute('src').replace("161", "845").replace("120", "633"))


                    print("Scraping completed.")
                except TimeoutError:
                    print("Main content not loaded in time.")
                finally:
                    browser.close()
            except TimeoutError:
                print("Timeout occurred for IAAI Scraper.")
                browser.close()

    
class BeForwardScrper(BaseScraper):
    def __init__(self,url,crop_size):
        super().__init__(url,crop_size)
    def scrape(self):
        with sync_playwright() as playwright:


                browser = playwright.chromium.launch(headless=False,args=[
                        "--window-position=-10000,-10000",  # Position window off-screen
                        "--disable-blink-features=AutomationControlled",
                    ])
                
                # Open a new page in the connected browser
                page = browser.new_page()
                
                # Go to the desired URL
                page.goto(self.url, wait_until="domcontentloaded", timeout=10000)
                # page.wait_for_selector("h1",timeout=10000)
                car_name_element = page.query_selector("div.car-info-flex-box")
                if car_name_element:
                    car_name = car_name_element.query_selector("h1")
                    if car_name:
                        self.car_name = car_name.inner_text()
                # self.data['Price'] = page.query_selector("span.price.ip-usd-price").inner_text()
                car_info_div = page.query_selector("div.cf.specs-area")
                car_info_table = car_info_div.query_selector("table.specification")
                rows = car_info_table.query_selector_all('tr')
                for row in rows:
                    
                    keys = row.query_selector_all('th')
                    values = row.query_selector_all('td')

                    self.data[keys[0].inner_text()] = values[0].inner_text()
                    if(len(keys)==2 and len(values)==2):
                        self.data[keys[1].inner_text()] = values[1].inner_text()
                image_next_button = page.query_selector("img[id='fn-vehicle-detail-images-slider-next']")


                while(True):
                    image_next_button.click()
                    image = "https:" + page.query_selector("img[id='mainImage']").get_attribute('src').replace("\n"," ")
                    if(image in self.images):
                        break
                    self.images.append(image)
                    



                browser.close()
                # Check for CAPTCHA

class SBTJapanScraper(BaseScraper):
    def __init__(self,url,crop_size):
        super().__init__(url,crop_size)
    def scrape(self):
        
        with sync_playwright() as playwright:



                browser = playwright.chromium.launch(headless=False,args=[
                        "--window-position=-10000,-10000",  # Position window off-screen
                        "--disable-blink-features=AutomationControlled",
                    ])
                

                page = browser.new_page()

                page.goto(self.url+"?currency=2")

                car_name_element = page.query_selector('div.content')
                if car_name_element:
                    car_name = car_name_element.query_selector("h2")
                    if car_name:
                        self.car_name = car_name.inner_text()
                car_details_divs = page.query_selector_all("div.carDetails")
                if(len(car_details_divs)>1):
                    car_details_div = car_details_divs[1]
                else:
                    car_details_div = car_details_divs[0]

                car_details_table = car_details_div.query_selector("table.tabA")
                
                
                rows = car_details_table.query_selector_all("tr")
                # self.data["Price: "] = page.query_selector("span[id='fob']").inner_text()
                for row in rows:
                    key = row.query_selector_all("th")
                    value = row.query_selector_all("td")

                    self.data[key[0].inner_text()] = value[0].inner_text()
                    self.data[key[1].inner_text()] = value[1].inner_text()

                

                image_div = page.query_selector("div.photoBox")
                images = image_div.query_selector_all("img")
                for img in images:
                    if(img.get_attribute('src')[-3:]=='640'):
                        self.images.append(img.get_attribute('src'))
                

                

                browser.close()


                


class ManheimScraper(BaseScraper):
    def __init__(self, url, crop_size, cookies_path="cookies.json"):
        super().__init__(url,crop_size)
        self.cookies_path = cookies_path
        self.images = []

    def save_cookies(self, page):
        try:
            cookies = page.context.cookies()
            with open(self.cookies_path, "w") as file:
                json.dump(cookies, file)
            print("Cookies saved successfully.")
        except Exception as e:
            print(f"Error saving cookies: {e}")

    def load_cookies(self, page):
        try:
            with open(self.cookies_path, "r") as file:
                cookies = json.load(file)
                page.context.add_cookies(cookies)
            print("Cookies loaded successfully.")
        except FileNotFoundError:
            print("No cookies file found, proceeding with login.")

    def check_login_required(self, page):
        sign_in = page.query_selector("h1")
        return sign_in and sign_in.inner_text() == "SIGN IN"

    def handle_login(self, playwright):
        # Launch browser in visible mode for user login
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        messagebox.showerror(message="You have been logged out. You will be redirected to login windows. You will 90 sec to login. Don't close the window after login it will automatically close after 90 seconds.")
        page.goto("https://auth.manheim.com/as/authorization.oauth2?adaptor=manheim_customer&client_id=smzbeqp277av7kx8jmx3syk9&redirect_uri=https%3A%2F%2Fhome.manheim.com%2Fcallback&response_type=code&scope=email+profile+openid+offline_access&state=%2Flogin")

        # Inform user and wait for login
        
        time.sleep(90)  # Give user time to log in

        # Save cookies after login
        self.save_cookies(page)
        browser.close()
    def scrape_auction_details(self,page):
        auction_info_element = page.query_selector("div.BidWidget__col1")
        details_mapping = {
            "Status":"span[data-test-id='status-label']",
            "Current Bid":"span.bid-widget__value.current-price",
            "Adj MMR": "a.MmrValuation__link",
            "Time Left": "span.bboEndStartTime",
            "Pick Up Location": "span[data-test-id='pickup-location-container']",
            "Vehicle Location": "span[data-test-id='vehicle-location-value']",
            "Seller": "span.bid-widget__value.bid-widget__value--seller-name"
  
                    }

                    # Extract data with handling for missing elements
        for key, selector in details_mapping.items():
            element = auction_info_element.query_selector(selector)
            if element:

                    self.data[key] = element.inner_text() 
      
        
        
    def scrape_car_details(self, page):
        car_name_element = page.query_selector("span.ListingTitle__title")
        if car_name_element:
            self.car_name = car_name_element.inner_text()
            print("Car Name:", self.car_name)

        car_details_element = page.query_selector("div[data-test-id='collapse-overview']")
        if car_details_element:
            columns = car_details_element.query_selector_all("div.dont-break-columns")
            for column in columns:
                key = column.query_selector("div.dt.collapsible-top-label")
                value = column.query_selector("div.dd,.collapsible-bottom-value")
                if key and value:
                    self.data[key.inner_text()] = value.inner_text()



    def scrape_images(self, page):
        image_element = page.query_selector("div[id='fyusion-prism-viewer']")
        next_button = image_element.query_selector("a.svfy_a_next")
        for _ in range(30):
            img = image_element.query_selector("img.svfy_img")
            if img:
                img_src = img.get_attribute('src')
                if img_src not in self.images:
                    self.images.append(img_src)
                else:
                    break
            if next_button:
                next_button.click()
                time.sleep(4)
            else:
                break

    def scrape(self):
        with sync_playwright() as playwright:
            # Start browser off-screen
            browser = playwright.chromium.launch(headless=False, args=["--window-position=-10000,-10000"])
            page = browser.new_page()
            self.load_cookies(page)
            page.goto(self.url, wait_until="domcontentloaded", timeout=10000)

            try:
                # Check if login is required
                if self.check_login_required(page):
                    browser.close()  # Close off-screen browser
                    self.handle_login(playwright)  # Relaunch on-screen for login
                    # Re-launch off-screen after login
                    browser = playwright.chromium.launch(headless=False, args=["--window-position=-10000,-10000"])
                    page = browser.new_page()
                    self.load_cookies(page)
                    page.goto(self.url)

                # Scrape data after login
                page.wait_for_selector("span.ListingTitle__title")
                self.scrape_auction_details(page)
                self.scrape_car_details(page)
                self.scrape_images(page)

            except Exception as e:
                print(f"An error occurred during scraping: {e}")
            finally:
                browser.close()




                    





 







            
def get_scraper(url):
    domain = urlparse(url).netloc
    if "copart.com" in domain:
        return CopartScraper(url,0)
    elif "iaai.com" in domain:
        return IAAIScraper(url,15)
    elif "beforward" in domain:
        return BeForwardScrper(url,25)
    elif "sbtjapan" in domain:
        return SBTJapanScraper(url,45)
    elif "manheim" in domain:
        return ManheimScraper(url,0)
    else:
        raise ValueError("Unsupported site")

# # Example Usage

if __name__ == "__main__":
    root = tk.Tk()
    app = CarScraperGUI(root)
    root.mainloop()







                
        

