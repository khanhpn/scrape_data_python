from bs4 import BeautifulSoup  # using this lib to scrape data
import requests
import csv
import json


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


class WriteToJson:
    def __init__(self, data):
        self.data = data

    def start(self):
        print("Starting write file json....")
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


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
        if original_price.find('del') == None and len(detail.select('.product-price > .pro-price')) == 0:
            product_detail["price"] = None
            return

        if len(detail.select('.product-price > .pro-price')) >= 0:
            product_detail["price"] = detail.select(
                '.product-price > .pro-price')[0].string
        else:
            product_detail["price"] = original_price.find(
                'del').string

    def get_category(self, detail, product_detail):
        original_category = detail.select(
            "ol.breadcrumb > li > a > span", {"itemprop": "name"})[1]
        if original_category != None:
            product_detail["original_category"] = original_category.string
        else:
            product_detail["original_category"] = None

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
            if product_detail["price"] == None:
                return

            self.get_category(detail, product_detail)

            if product_detail["original_category"] == None:
                print("**********************************")
                print("This link have not category %s" % product)
                print("**********************************")
                return

            images = detail.select(
                'a[class="product-gallery__thumb-placeholder"]')
            image_list = []
            for image in images:
                image_list.append("https:" + image.img["data-image"])
            product_detail["images"] = ",".join(image_list)

            product_detail["name"] = detail.h1.string
            product_detail["Sku"] = sku.string
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
        # return [self.parse_product("https://bicicosmetics.vn/products/nuoc-hoa-hong-klairs-supple-preparation-facial-toner")]
        arr_products = []
        for products in products_link:
            for product in products:
                try:
                    arr_products.append(self.parse_product(product))
                except:
                    print(product)
                    continue

        return self.format_json(arr_products)

    def format_json(self, products):
        print("**********************************************************")
        print("Starting to filter and convert data to json")
        object_products = []
        # list categories
        categories = list(set([product["original_category"]
                               for product in products]))
        object_products.append({"categories": categories})
        for category in categories:
            dic_category = {}
            dic_category[category] = []
            for product in products:
                if product["original_category"] == category:
                    dic_category[category].append(product)
            object_products.append(dic_category)

        print("End to filter and convert data to json")
        print("**********************************************************")
        return object_products


url = "https://bicicosmetics.vn"
categories = [url + '/collections/hang-moi-ve']
base = Bicicosmetics(url, categories)
data = base.main()

file_json = WriteToJson(data)
file_json.start()

# file_csv = WriteCsvFile(data)
# file_csv.start()
