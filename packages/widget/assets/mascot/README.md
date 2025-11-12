# マスコット画像ディレクトリ

このディレクトリには、ウィジェットで使用するマスコット画像を配置します。

## 使用方法

1. マスコット画像ファイル（PNG、JPG、SVG、WebPなど）をこのディレクトリに配置します。

2. ウィジェットの初期化時に、画像のURLを指定します：

```javascript
ragChat('init', {
  tenantId: 'YOUR_TENANT_ID',
  apiKey: 'YOUR_API_KEY',
  mascot: {
    type: 'image',
    url: 'http://localhost:3001/assets/mascot/your-mascot.png'
  }
});
```

## 将来の3Dモデル対応

将来的には、3Dモデル（GLB、GLTF形式）もこのディレクトリに配置し、以下のように使用できます：

```javascript
ragChat('init', {
  tenantId: 'YOUR_TENANT_ID',
  apiKey: 'YOUR_API_KEY',
  mascot: {
    type: 'model3d',
    url: 'http://localhost:3001/assets/mascot/your-mascot.glb',
    animation: true
  }
});
```

## ファイル形式

- **画像**: PNG, JPG, JPEG, GIF, SVG, WebP
- **3Dモデル**: GLB, GLTF（将来対応予定）

