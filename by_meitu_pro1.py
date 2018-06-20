import requests
import gevent
from lxml import html
from gevent import monkey


monkey.patch_all()


# 构建函数，用来查找该页内所有图片集的详细地址。目前一页包含15组套图，所以应该返回包含15个链接的序列。
def get_page_number(num):
    # 构造每个分页的网址
    url = 'http://www.mmjpg.com/home/' + num

    response = requests.get(url).content
    # 调用requests库，获取二进制的相应内容。注意，这里使用.text方法的话，下面的html解析会报错，大家可以试一下。这里涉及到.content和.text的区别了。简单说，如果是处理文字、链接等内容，建议使用.text，处理视频、音频、图片等二进制内容，建议使用.content。
    selector = html.fromstring(response)
    # 使用lxml.html模块构建选择器，主要功能是将二进制的服务器相应内容response转化为可读取的元素树（element tree）。
    # lxml中就有etree模块，是构建元素树用的。如果是将html字符串转化为可读取的元素树，就建议使用lxml.html.fromstring，毕竟这几个名字应该能大致说明功能了吧。
    urls = []
    # 准备容器
    for i in selector.xpath("//ul/li/a/@href"):
        # 利用xpath定位到所有的套图的详细地址
        urls.append(i)
    # 遍历所有地址，添加到容器中
    return urls
    # 将序列作为函数结果返回


def get_image_detail(url):
    response = requests.get(url).content
    selector = html.fromstring(response)
    # 获取图片标题
    image_title = selector.xpath("//h2/text()")[0]
    # 获取图片数量
    image_amount = selector.xpath("//div[@class='page']/a[last()-1]/text()")[0]
    # 获取图片图片详细地址
    image_detail_websites = []  # 存放图片具体地址的容器
    for i in range(int(image_amount)):
        image_detail_link = '{}/{}'.format(url, i + 1)
        response = requests.get(image_detail_link).content
        sel = html.fromstring(response)
        # 单张图片的最终下载地址
        image_download_link = sel.xpath("//div[@class='content']/a/img/@src")[0]
        # print(image_download_link)
        image_detail_websites.append(image_download_link)

    return image_title, image_detail_websites


def download_image(pag_number, image_title, image_detail_websites):
    # 将图片保存到本地。传入的两个参数是图片的标题，和下载地址序列

    num = 1

    amount = len(image_detail_websites)

    # 获取图片总数

    for i in image_detail_websites:
        filename = 'pic/'+'%s%s.jpg' % (image_title, num)

        print('正在下载图片：第%s页的--%s第%s/%s张，' % (pag_number, image_title, num, amount))

        with open(filename, 'wb') as f:
            # ***
            header = {'Referer': 'http://www.mmjpg.com/home/2',

                      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}

            f.write(requests.get(i, headers=header).content)

        num += 1


if __name__ == '__main__':
    img_list = []
    # 目前第一页有bug , 只能从第二页开始下载
    for page_number in range(2, 30):
        for link in get_page_number(str(page_number)):
            img_title, img_websites = get_image_detail(link)
            img_list.append(gevent.spawn(download_image, page_number, img_title, img_websites))

        gevent.joinall(img_list)  # joinall等待所有协程执行完毕
