from pathlib import Path
import yaml

cfg = Path.home() / '.config' / 'md2wechat' / 'config.yaml'
data = yaml.safe_load(cfg.read_text(encoding='utf-8'))
api = data.setdefault('api', {})
api['image_provider'] = 'openai'
api['image_base_url'] = 'https://api-xai.ainaibahub.com/v1'
api['image_model'] = 'gpt-image-2'
api['image_size'] = '1792x1024'
api['image_key'] = 'sk-XvsVyVM57ZHeR0t0rHax3sGee5GPRiwNquVDMNj4ZPagySfN'
cfg.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
print(cfg)
