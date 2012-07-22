from BeautifulSoup import BeautifulSoup as BS, Tag

def enml2html(note):
    enml = note.content
    resources = set(note.resources.all())
    soup = BS(enml)
    note = getattr(soup, 'en-note')
    print str(note)
    for media in note.findAll('en-media'):
        hash = media['hash']
        for res in resources:
            if res.hash == hash:
                mime_type = media['type']
                if mime_type.startswith('image/'):
                    img = Tag(soup, 'img')
                    img['height'] = media.get('height', 450)
                    img['width'] = media.get('width', 600)
                    img['src'] = res.file.url
                    media.replaceWith(img)
                    break
    note.name = 'div'
    del note['style']
    return str(note)

if __name__ == '__main__':
    from enote.models import Note
    import sys
    note = Note.objects.get(guid=sys.argv[1])
    print enml2html(note)
