from pathlib import Path
import yaml

cfg = Path.home() / '.config' / 'md2wechat' / 'config.yaml'
text = cfg.read_text(encoding='utf-8')
data = yaml.safe_load(text)
api = data.setdefault('api', {})
api['image_provider'] = 'openai'
api['image_base_url'] = 'https://api-xai.ainaibahub.com/v1'
api['image_model'] = 'gpt-image-2'
api['image_size'] = '1792x1024'
# Reuse the active key field for the OpenAI-compatible upstream.
api['image_key'] = api.get('md2wechat_key', api.get('image_key', ''))
cfg.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding='utf-8')
print(cfg)
