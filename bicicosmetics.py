from bs4 import BeautifulSoup  # using this lib to scrape data
import requests
import csv


class WriteCsvFile:
    def __init__(self, data):
        self.data = data

    def start(self):
        print("Starting write file csv....")
        with open('data.csv', mode='w') as csv_file:
            fieldnames = ['TenSP', 'Ma', 'Danh Muc', 'Xuat Xu',
                          'Thuong Hieu', 'Giam gia', 'Gia ban', 'Image']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for item in self.data:
                try:
                    writer.writerow({'TenSP': item["TenSP"], 'Ma': item["sku"], 'Danh Muc': item["category"],
                                     'Xuat Xu': item["original"], 'Thuong Hieu': item["brand"], 'Giam gia': item["sale_price"],
                                     'Gia ban': item["price_original"], 'Image': item["images"]})
                except:
                    print(item)
                    continue
        print("Finish write file csv....")


class Bicicosmetics:
    def __init__(self, url, categories):
        self.url = url
        self.categories = categories

    def base_soup(self, link):
        html_content = requests.get(link).text
        return BeautifulSoup(html_content, "html.parser")

    # get all paging in products
    def get_products_paging(self):
        products = []
        for category in self.categories:
            category_link = self.base_soup(category)
            total_page = self.get_total(category_link)

            for page in range(1, total_page):
                products.append(category + "?page=" + str(page))
                print("Start crawl link:" + category + "?page=" + str(page))

        return products

    # get total paging in each categories
    def get_total(self, object_category):
        total_page_node = object_category.find_all(
            "a", attrs={"class", "page-node"})
        return int(total_page_node[-1].text)

    # get all products link for each page
    def get_link_paging_products(self, products):
        links = []
        for item in products:
            try:
                page = self.base_soup(item)
                items = page.find_all("a", attrs={"class", "image-resize"})
                links.append(self.get_product_per_page(items))
            except:
                print("Error this link" + item)
        return links

    # get all product in per page
    def get_product_per_page(self, products):
        links = []
        try:
            for item in products:
                product_url = self.url + item["href"]
                print("Start parse this link:" + product_url)
                links.append(product_url)
        except:
            print("Error this link" + item)
        return links

    # parse price
    def parse_price(self, detail, product_detail):
        original_price = detail.find(id='price-preview')
        if original_price.find('del') == None:
            product_detail["price_original"] = ''
        else:
            product_detail["price_original"] = original_price.find(
                'del').string

        if len(detail.select('.product-price > .pro-sale')) == 0:
            product_detail["sale_price"] = detail.select(
                '.product-price > .pro-price')[0].string
        else:
            sale_price = detail.select('.product-price > .pro-sale')[0].text
            product_detail["sale_price"] = sale_price

    # parse a product to get detail
    def parse_product(self, product):
        product_detail = {}
        try:
            print("Start parse detail this link:" + product)
            detail = self.base_soup(product)

            sku = detail.find("span", attrs={"class", "sku"})
            product_detail["sku"] = sku.string
            info = detail.find("div", attrs={"class", "product_meta_wrapper"})

            self.parse_price(detail, product_detail)

            images = detail.select(
                'a[class="product-gallery__thumb-placeholder"]')
            image_list = []
            for image in images:
                image_list.append("https:" + image.img["data-image"])
            product_detail["images"] = ",".join(image_list)

            product_detail["TenSP"] = detail.h1.string
            product_detail["Ma"] = sku.string
            obj_table = info.findChildren('table')[0]

            original = obj_table.find(
                "td", text="Xuất xứ:")
            original = '' if original == None else original.find_next_sibling(
                "td")
            product_detail["original"] = original.string

            brand = obj_table.find(
                "td", text="Thương hiệu:")
            brand = '' if brand == None else brand.find_next_sibling("td")
            product_detail["brand"] = brand.string

            title = obj_table.find(
                "td", text="Tiêu đề:")
            title = '' if title == None else title.find_next_sibling("td")

            category = obj_table.find(
                "td", text="Danh mục:")
            category = '' if category == None else category.find_next_sibling(
                "td")
            category = ''.join([x.text for x in category.find_all("a")])
            product_detail["category"] = category
            print("End parse detail this link:" + product)

        except:
            print("Error this link" + product)
        return product_detail

    def main(self):
        products = self.get_products_paging()
        products_link = self.get_link_paging_products(products)
        # return [self.parse_product("https://bicicosmetics.vn/products/mat-na-ngu-dr-jart-dermask-sleeping-mask")]
        arr_products = []
        for products in products_link:
            for product in products:
                try:
                    arr_products.append(self.parse_product(product))
                except:
                    print(product)
                    continue
        return arr_products


url = "https://bicicosmetics.vn"
categories = [url + '/collections/hang-moi-ve']
base = Bicicosmetics(url, categories)
data = base.main()

file_csv = WriteCsvFile(data)
file_csv.start()
