import {LitElement,html,css,nothing} from 'lit';
import {customElement,state,property} from 'lit/decorators.js';
import {styleMap} from 'lit/directives/style-map.js';
import {choose,rpc,openFile,bytes,date,basename,desktop,type Folder,type MediaFile,type SearchResponse,type Status} from './api';
import {styles} from './styles';
import './release-controls';
import './update-controls';
import type {ReleaseControls} from './release-controls';

@customElement('media-thumbnail')
class Thumbnail extends LitElement {
  @property({type:Number}) fileId=0;
  @state() private url='';
  @state() private failed=false;
  private observer?:IntersectionObserver;
  static styles=css`:host{display:block;overflow:hidden}img{width:100%;height:100%;object-fit:cover;display:block}span{height:100%;display:grid;place-items:center;color:#7f8b9b;font:12px 'Segoe UI',sans-serif}`;
  connectedCallback(){super.connectedCallback();this.observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){this.observer?.disconnect();void this.load()}},{rootMargin:'250px'});this.observer.observe(this)}
  disconnectedCallback(){this.observer?.disconnect();super.disconnectedCallback()}
  updated(changed:Map<string,unknown>){if(changed.has('fileId')&&changed.get('fileId')!==undefined){this.url='';this.failed=false;void this.load()}}
  private async load(){const id=this.fileId;try{const result=await rpc<{url:string}>('preview',{id,thumbnail:true});if(this.isConnected&&this.fileId===id)this.url=result.url}catch{this.failed=true}}
  render(){return this.url?html`<img src=${this.url} alt="" loading="lazy" decoding="async">`:html`<span>${this.failed?'画像を読み込めません':'読み込み中'}</span>`}
}

@customElement('media-search-app')
class App extends LitElement {
  static styles=styles;
  @state() private folders:Folder[]=[];
  @state() private status?:Status;
  @state() private results:SearchResponse={items:[],total:0,offset:0,semantic:false};
  @state() private query='';
  @state() private imageQuery='';
  @state() private filename='';
  @state() private format='';
  @state() private dateAfter='';
  @state() private dateBefore='';
  @state() private view:'grid'|'list'='grid';
  @state() private error='';
  @state() private busy=false;
  @state() private preview?:{url:string;file:MediaFile};
  @state() private zoom=1;
  @state() private previewBaseWidth=0;
  @state() private theme=localStorage.getItem('theme')||'system';
  @state() private settingsModel='';
  @state() private settingsBackend='gpu';
  private timer?:ReturnType<typeof setInterval>;
  private polling=false;
  private searched=false;
  private keyboard=(event:KeyboardEvent)=>{if((event.ctrlKey||event.metaKey)&&event.key==='k'){event.preventDefault();this.renderRoot.querySelector<HTMLInputElement>('#query')?.focus()}else if(event.ctrlKey&&event.key==='w'){event.preventDefault();void this.run(()=>desktop('close'))}else if(event.key==='F1'){event.preventDefault();void this.help()}};
  connectedCallback(){super.connectedCallback();window.addEventListener('keydown',this.keyboard);void this.initialize();this.timer=setInterval(()=>void this.poll(),1500);this.applyTheme()}
  disconnectedCallback(){super.disconnectedCallback();window.removeEventListener('keydown',this.keyboard);clearInterval(this.timer)}
  private applyTheme(){const dark=this.theme==='dark'||this.theme==='system'&&matchMedia('(prefers-color-scheme: dark)').matches;this.setAttribute('theme',dark?'dark':'light');localStorage.setItem('theme',this.theme)}
  private async initialize(){try{await this.refresh();await this.search()}catch(e){this.error=String(e)}}
  private async run(action:()=>Promise<unknown>){try{await action()}catch(e){this.error=String(e)}}
  private async refresh(){const [status,folders]=await Promise.all([rpc<Status>('status'),rpc<Folder[]>('folders')]);this.status=status;this.folders=folders}
  private async poll(){if(this.polling||this.busy)return;this.polling=true;try{const wasRunning=this.status?.running;await this.refresh();if(wasRunning&&!this.status?.running)await this.search(this.results.offset)}catch(e){this.error=String(e)}finally{this.polling=false}}
  private async addFolder(){await this.run(async()=>{const path=await choose('folder');if(!path)return;this.folders=await rpc<Folder[]>('add_folder',{path});await this.refresh()})}
  private async folderAction(folder:Folder,action:string){await this.run(async()=>{if(action==='remove'&&!confirm(`「${folder.path}」を検索対象から外します。元の写真は変更しません。`))return;await rpc('folder_action',{id:folder.id,action,enabled:!folder.enabled});await this.refresh();await this.search()})}
  private async index(){await this.run(async()=>{await rpc('start');await this.refresh()})}
  private async pause(){await this.run(async()=>{await rpc('pause');await this.refresh()})}
  private async search(offset=0){if(this.busy)return;this.busy=true;this.error='';try{this.results=await rpc<SearchResponse>('search',{text:this.query,image:this.imageQuery,filename:this.filename,format:this.format,after:this.dateAfter,before:this.dateBefore,offset,limit:60});this.searched=true;this.renderRoot.querySelector('.results')?.scrollTo({top:0})}catch(e){this.error=String(e)}finally{this.busy=false}}
  private async imageSearch(){await this.run(async()=>{const path=await choose('image');if(!path)return;this.imageQuery=path;this.query='';await this.search()})}
  private async showPreview(file:MediaFile){await this.run(async()=>{this.preview=await rpc<{url:string;file:MediaFile}>('preview',{id:file.id});this.zoom=1;this.previewBaseWidth=0;await this.updateComplete;this.renderRoot.querySelector<HTMLDialogElement>('#preview')?.showModal();requestAnimationFrame(()=>{const image=this.renderRoot.querySelector<HTMLImageElement>('#preview img');if(image?.complete)this.fitPreview(image)})})}
  private fitPreview(image:HTMLImageElement){const container=this.renderRoot.querySelector<HTMLElement>('.preview-image');if(container&&image.naturalWidth&&container.clientHeight){this.previewBaseWidth=Math.min(image.naturalWidth,container.clientWidth,container.clientHeight*image.naturalWidth/image.naturalHeight)}}
  private async settings(){this.settingsModel=this.status?.config.model_path||'';this.settingsBackend=this.status?.config.backend||'gpu';await this.updateComplete;this.renderRoot.querySelector<HTMLDialogElement>('#settings')?.showModal()}
  private async help(){await this.updateComplete;await this.renderRoot.querySelector<ReleaseControls>('release-controls[mode=assistant]')?.openHelp()}
  private closeDialog(id:string){this.renderRoot.querySelector<HTMLDialogElement>(id)?.close()}
  private async saveSettings(){await this.run(async()=>{await rpc('configure',{model_path:this.settingsModel,backend:this.settingsBackend});this.closeDialog('#settings');await this.refresh()})}
  private async pickModel(){await this.run(async()=>{const path=await choose('model');if(path)this.settingsModel=path})}
  private phase(){const phases:Record<string,string>={waiting_idle:'PCの操作が止まるのを待機中',idle:'解析待機中',loading:'モデルを読み込み中',scanning:'追加・変更を確認中',indexing:'写真を解析中',pausing:'現在の写真を保存して停止中',paused:'解析を一時停止',error:'解析でエラーが発生'};return phases[this.status?.progress.phase||'idle']}
  render(){const s=this.status;const start=this.results.offset;const total=this.results.total;const done=s?.jobs.done||0;const pending=(s?.jobs.pending||0)+(s?.jobs.processing||0);return html`
<div class="layout">
<aside><div class="brand">SakuLoca<small>サクロカ · このPCで処理</small></div>
<div class="side-label">検索フォルダー <button class="quiet" @click=${this.addFolder} ?disabled=${s?.running} aria-label="フォルダーを追加">＋</button></div>
<div class="folders">${this.folders.map(f=>html`<div class="folder"><div class="folder-line"><input type="checkbox" aria-label=${`${f.path} を検索対象にする`} .checked=${!!f.enabled} ?disabled=${s?.running} @change=${()=>this.folderAction(f,'enable')}><span class="folder-name" title=${f.path}>${basename(f.path)}</span><button class="quiet" title="検索対象から削除" ?disabled=${s?.running} @click=${()=>this.folderAction(f,'remove')}>×</button></div><div class="folder-path">${f.path}</div><div class="folder-state">${f.count}枚${f.status==='offline'?' · 未接続':f.status==='partial'?' · 一部アクセス不可':''}</div>${f.error?html`<div class="folder-state">${f.error}</div>`:nothing}</div>`)}${!this.folders.length?html`<p class="note">写真のあるフォルダーを登録すると、ここに表示されます。</p>`:nothing}</div>
<div class="side-bottom"><button @click=${this.addFolder} ?disabled=${s?.running}>フォルダーを追加</button><button @click=${this.settings}>モデルと設定</button><button @click=${this.help}>ヘルプ / アプリ情報</button><div class="note"><span class="status-dot"></span>完全ローカル処理<br>検索データ ${bytes((s?.database_bytes||0)+(s?.cache_bytes||0)+(s?.runtime_cache_bytes||0))}</div></div></aside>
<main><header class="top"><h1>思い出を、言葉で見つける</h1><p class="subtitle">「海辺の風景」「赤いりんご」など、探したい写真を日本語で入力。</p>
<form class="search" @submit=${(e:Event)=>{e.preventDefault();this.imageQuery='';void this.search()}}><input id="query" class="search-input" aria-label="写真を自然言語で検索" placeholder="どんな写真を探しますか？" .value=${this.query} @input=${(e:Event)=>this.query=(e.target as HTMLInputElement).value}><button type="button" @click=${this.imageSearch} ?disabled=${this.busy}>画像で探す</button><button class="primary" ?disabled=${this.busy}>${this.busy?'検索中…':'検索'}</button></form>
${this.imageQuery?html`<div class="image-query">参照画像：${basename(this.imageQuery)} <button class="quiet" @click=${()=>{this.imageQuery='';void this.search()}}>解除 ×</button></div>`:nothing}
<div class="filters"><label>ファイル名 <input class="filename" placeholder="名前の一部" .value=${this.filename} @change=${(e:Event)=>{this.filename=(e.target as HTMLInputElement).value;void this.search()}}></label><label>形式 <select .value=${this.format} @change=${(e:Event)=>{this.format=(e.target as HTMLSelectElement).value;void this.search()}}><option value="">すべて</option><option value="jpg">JPEG</option><option value="jpeg">JPEG (.jpeg)</option><option value="png">PNG</option><option value="webp">WebP</option></select></label><label>更新日 <input aria-label="更新日の開始" type="date" .value=${this.dateAfter} @change=${(e:Event)=>{this.dateAfter=(e.target as HTMLInputElement).value;void this.search()}}> 〜 <input aria-label="更新日の終了" type="date" .value=${this.dateBefore} @change=${(e:Event)=>{this.dateBefore=(e.target as HTMLInputElement).value;void this.search()}}></label><span class="kbd">Ctrl + K で検索</span></div></header>
${this.error||s?.progress.last_error?html`<div class="error" role="alert"><span>${this.error||s?.progress.last_error}</span><button class="quiet" @click=${()=>this.error=''} aria-label="エラーを閉じる">×</button></div>`:nothing}
<div class="toolbar"><div><strong>${total.toLocaleString()}枚</strong> <span>${this.results.semantic?'意味の近い順 · 類似度は正解率ではありません':'更新日時の新しい順'}</span></div><div class="view-buttons"><button class=${this.view==='grid'?'active':''} aria-label="グリッド表示" @click=${()=>this.view='grid'}>▦</button><button class=${this.view==='list'?'active':''} aria-label="リスト表示" @click=${()=>this.view='list'}>☰</button></div></div>
<section class=${`results ${this.busy?'loading':''}`} aria-label="検索結果" aria-busy=${this.busy}>${total?html`<div class=${this.view}>${this.results.items.map(file=>html`<button class="card" @click=${()=>this.showPreview(file)} aria-label=${`${file.name} をプレビュー`}><media-thumbnail .fileId=${file.id}></media-thumbnail><div class="card-info"><div class="card-name" title=${file.name}>${file.name}</div><div class="card-meta">${file.format.toUpperCase()} · ${bytes(file.size)}${file.score!==undefined?` · 類似度 ${file.score.toFixed(3)}`:''}</div>${this.view==='list'?html`<div class="card-meta">${date(file.mtime_ns)} · ${file.path}</div>`:nothing}</div></button>`)}</div>`:html`<div class="empty"><div class="empty-icon">▧</div><h2>${!s?.model_bytes?'AIモデルを準備しましょう':done?'検索条件に一致する写真がありません':this.folders.length?'写真を検索する準備をしましょう':'最初のフォルダーを登録'}</h2><p>${!s?.model_bytes?'「モデルと設定」で既存モデルを選択するか、公式配布から取得してください。':done?'検索語やフィルターを変えてお試しください。':this.folders.length?'「差分更新 / 解析」を押すと、登録したフォルダーだけを解析します。解析後、言葉や画像から写真を探せます。':'写真のあるフォルダーを選んでください。サブフォルダーも対象になります。'}</p>${!s?.model_bytes?html`<button class="primary" @click=${this.settings}>モデルと設定</button>`:done?nothing:this.folders.length?html`<button class="primary" @click=${this.index} ?disabled=${s?.running}>差分更新 / 解析</button>`:html`<button class="primary" @click=${this.addFolder}>フォルダーを追加</button>`}${this.searched&&this.query?html`<p>検索条件に一致する解析済みの写真はありません。</p>`:nothing}</div>`}</section>
<footer><div><div class=${s?.running?'busy':''}>${this.phase()} ${s?.running?html`<progress max=${Math.max(done+pending,1)} value=${done}></progress>`:nothing}</div><div class="progress-text">解析済み ${done}枚 · 待ち ${pending}枚 · エラー ${s?.jobs.error||0}件${s?.running?` · ${s.speed.toFixed(2)}枚/秒`:''}</div></div><div class="pager">${total>60?html`<button ?disabled=${start===0||this.busy} @click=${()=>this.search(Math.max(0,start-60))}>前へ</button><span>${start+1}–${Math.min(start+60,total)} / ${total}</span><button ?disabled=${start+60>=total||this.busy} @click=${()=>this.search(start+60)}>次へ</button>`:nothing}${s?.running?html`<button @click=${this.pause}>一時停止</button>`:html`<button @click=${this.index} ?disabled=${!s?.model_bytes||!this.folders.some(f=>f.enabled)}>差分更新 / 解析</button>`}</div></footer></main></div>
<dialog id="settings"><div class="dialog-header"><h2>モデルと設定</h2><button class="quiet" @click=${()=>this.closeDialog('#settings')} aria-label="設定を閉じる">×</button></div><release-controls .status=${s} @refresh-needed=${()=>this.refresh()}></release-controls><update-controls></update-controls><div class="setting"><label>表示テーマ</label><select aria-label="表示テーマ" .value=${this.theme} @change=${(e:Event)=>{this.theme=(e.target as HTMLSelectElement).value;this.applyTheme()}}><option value="system">Windowsの設定に合わせる</option><option value="light">ライト</option><option value="dark">ダーク</option></select></div><div class="dialog-actions"><button @click=${()=>this.closeDialog('#settings')}>閉じる</button></div></dialog>
<release-controls mode="assistant" .status=${s} @refresh-needed=${()=>this.refresh()}></release-controls>
<dialog id="preview" class="preview-dialog"><div class="dialog-header"><strong>${this.preview?.file.name}</strong><button class="quiet" @click=${()=>this.closeDialog('#preview')} aria-label="プレビューを閉じる">×</button></div><div class="preview-tools"><button @click=${()=>this.zoom=Math.max(.25,this.zoom-.25)} aria-label="縮小">−</button><span>${Math.round(this.zoom*100)}%</span><button @click=${()=>this.zoom=Math.min(4,this.zoom+.25)} aria-label="拡大">＋</button><button @click=${()=>this.zoom=1}>画面に合わせる</button><span class="space"></span><button @click=${()=>this.run(async()=>{this.imageQuery=this.preview!.file.path;this.query='';this.closeDialog('#preview');await this.search()})}>この写真に似た画像</button><button @click=${()=>this.run(()=>openFile(this.preview!.file.id))}>元のファイルを開く</button><button @click=${()=>this.run(()=>openFile(this.preview!.file.id,true))}>保存場所を開く</button></div><div class="preview-image"><div class="preview-canvas">${this.preview?html`<img src=${this.preview.url} alt=${this.preview.file.name} @load=${(event:Event)=>this.fitPreview(event.target as HTMLImageElement)} style=${styleMap({width:this.previewBaseWidth?`${this.previewBaseWidth*this.zoom}px`:'auto',maxWidth:this.previewBaseWidth?'none':'100%',maxHeight:this.previewBaseWidth?'none':'100%'})}>`:nothing}</div></div>${this.preview?html`<div class="preview-info"><span>${date(this.preview.file.mtime_ns)}</span><span>${bytes(this.preview.file.size)}</span><span>${this.preview.file.format.toUpperCase()}</span></div><div class="path">${this.preview.file.path}</div>`:nothing}</dialog>`}
}
