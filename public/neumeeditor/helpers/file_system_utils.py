from cantusdata.settings import MEDIA_ROOT, MEDIA_URL


def media_url_to_system_path(media_path):
    """
    Given a public media file url, get the system path of the file.

    :param media_path: public relative url of media file
    :return: the system path of the file
    """
    return MEDIA_ROOT + remove_media_url(media_path)

def remove_media_url(media_path):
    """
    Strip leading MEDIA_URL from a media file url.

    :param media_path:
    :return:
    """
    if media_path.startswith(MEDIA_URL):
        return media_path[len(MEDIA_URL):]
    else:
        return media_path
