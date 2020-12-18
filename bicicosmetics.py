from bs4 import BeautifulSoup  # using this lib to scrape data
import requests
import csv
import json
from uuid import uuid4


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
    def __init__(self, data, cat):
        self.data = data
        self.cat = cat

    def start(self):
        print("Starting write file json....")
        filename = self.cat + ".json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)


class Bicicosmetics:
    def __init__(self, url, category):
        self.url = url + category[0]
        self.category = category

    def base_soup(self, link):
        html_content = requests.get(link).text
        return BeautifulSoup(html_content, "html.parser")

    # get all paging in products
    def get_products_paging(self):
        products = []
        # for category in self.categories:
        # category_link = self.base_soup(self.url)
        # total_page = self.get_total(category_link)

        for page in range(1, 20):
            products.append(self.url + "?page=" + str(page))
            print("Start crawl link:" +
                  self.category[0] + "?page=" + str(page))

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
                links.append(product_url)
        except:
            print("Error this link" + item)
        return links

    # parse price
    def parse_price(self, detail, product_detail):
        original_price = detail.find(id='price-preview')
        if original_price.find('del') == None and len(detail.select('.product-price > .pro-price')) == 0:
            product_detail["Giaban"] = None
            return

        if len(detail.select('.product-price > .pro-price')) >= 0:
            product_detail["Giaban"] = detail.select(
                '.product-price > .pro-price')[0].string
        else:
            product_detail["Giaban"] = original_price.find(
                'del').string

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
            if product_detail["Giaban"] == None:
                return
            product_detail["category"] = self.category[1]

            images = detail.select(
                'a[class="product-gallery__thumb-placeholder"]')
            image_list = []
            for image in images:
                image_list.append("https:" + image.img["data-image"])
            product_detail["images"] = ",".join(image_list)
            product_detail["image"] = image_list[0]

            product_detail["TenSP"] = detail.h1.string
            product_detail["Ma"] = sku.string
            obj_table = info.findChildren('table')[0]

            original = obj_table.find(
                "td", text="Xuất xứ:")
            original = '' if original == None else original.find_next_sibling(
                "td")
            product_detail["XuatXu"] = original.string

            brand = obj_table.find(
                "td", text="Thương hiệu:")
            brand = '' if brand == None else brand.find_next_sibling("td")
            product_detail["ThuongHieu"] = brand.string

            title = obj_table.find(
                "td", text="Tiêu đề:")
            title = '' if title == None else title.find_next_sibling("td")

            category_obj = obj_table.find(
                "td", text="Danh mục:")
            category_obj = '' if category_obj == None else category_obj.find_next_sibling(
                "td")
            category_obj = ''.join(
                [x.text for x in category_obj.find_all("a")])
            product_detail["DanhMuc"] = category_obj
            product_detail["Id"] = str(uuid4())
            print("End parse detail this link:" + product)

        except:
            print("Error this link" + product)
        return product_detail

    def main(self):
        products = self.get_products_paging()
        products_link = self.get_link_paging_products(products)
        # return [self.parse_product("https://bicicosmetics.vn/collections/skincare/products/kem-chong-nang-hang-ngay-innisfree-intensive-triple-shield-sunscreen-spf50-pa-50ml")]
        arr_products = []
        for products in products_link:
            for product in products:
                try:
                    arr_products.append(self.parse_product(product))
                except:
                    print(product)
                    continue
        return arr_products

        # return self.format_json(arr_products)

    def format_json(self, products):
        print("**********************************************************")
        print("Starting to filter and convert data to json")
        object_products = []
        dic_category = {}
        dic_category[self.category[1]] = []
        for product in products:
            dic_category[self.category[1]].append(product)
        object_products.append(dic_category)

        print("End to filter and convert data to json")
        print("**********************************************************")
        return object_products


categories = [
    ['face-make-up', 'FaceMakeUp'],
    ['lips-make-up', 'LipsMakeUp'],
    ['eyes-make-up', 'EyesMakeUp'],
    ['sua-rua-mat', 'SuaRuaMat'],
    ['kem-chong-nang', 'KemChongNang'],
    ['mat-na-ngu', 'MatNaNgu'],
    ['kem-duong-mat', 'KemDuongMat'],
    ['mat-na', 'MatNa'],
    ['tay-trang', 'TayTrang'],
    ['kem-duong-da', 'KemDuongDa'],
    ['lotion', 'Lotion'],
    ['toner-nuoc-hoa-hong', 'TonerNuocHoaHong'],
    ['essense-serum-ampoule', 'EssenseSerumAmpoule'],
    ['tay-te-bao-chet', 'TayTeBaoChet'],
    ['xit-khoang', 'XitKhoang'],
    ['tri-mun-tri-tham', 'TriMunTriTham'],
    ['bo-kit-dung-thu', 'BoKitDungThu'],
    ['other', 'Other'],
]
url = "https://bicicosmetics.vn/collections/"
for cat in categories:
    base = Bicicosmetics(url, cat)
    data = base.main()

    file_json = WriteToJson(data, cat[1])
    file_json.start()


# file_csv = WriteCsvFile(data)
# file_csv.start()
