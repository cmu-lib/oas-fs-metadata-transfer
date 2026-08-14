from pathlib import Path
from transfer.models import useDevSettings

is_dev = useDevSettings.objects.first() #based on the admin setting, where this is set, determine which secret file to use.

how_many_oa_messages = '50'
institution_ror = "https://ror.org/05x2bcf33"

if is_dev.use_dev:# use dev settings.
    figshare_user = 2439005
    figshare_group_id = 57416
    in_copyright_num = 44
    
else:           # use prod settings
    figshare_user = 22087106
    figshare_group_id = 59231
    in_copyright_num = 43
