from bs4 import BeautifulSoup

# ADD YOUR OWN CUSTOM PARSERS

# Takes in raw html, parses it to return the main content (which will be fed into the model)
def parse_html_to_txt_cna(html):

    soup = BeautifulSoup(html, "html.parser")

    def isInFooter(tag):
        footer_attrs = ['Article page App widget', 'Article page whatsapp', 'Article page Newsletter', 'Copyright block']
        for parent in tag.parents:
            if 'data-title' in parent.attrs:
                if parent['data-title'] in footer_attrs: return True
        return False

    content = '\n'.join([p.string for p in soup.find_all('p') if p.string and not isInFooter(p)])
    return content