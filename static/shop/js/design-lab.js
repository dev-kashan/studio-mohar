/* =====================================================================
   DESIGN LAB (2026 redesign) - page: shop/templates/shop/design_lab.html
   Flow from the client's "Design Lab Redesign" file:
     1 Choose your merch -> 2 Choose your style (only if more than one)
     -> 3 Choose your colour -> 4 Editor -> 5 Your price -> "You're almost there!"
   The editor draws on the real colour photo of each side (front, back,
   sleeves). Every side has its own design area (fabric.js canvas) that
   covers the WHOLE photo of that side, so customers can design anywhere
   (also on the sleeves). A design is stored in
   "design units" (600 wide), so it moves to another product unchanged.
   Price = (size price + print price of each side with artwork) x promo
           x quantity tier + embroidery price x embroidered artworks.
   The same formula runs on the server (views._dl_quote).
   ===================================================================== */
(function () {
    'use strict';

    var DATA = JSON.parse(document.getElementById('dlData').textContent);
    var SIDES = ['front', 'back', 'left_sleeve', 'right_sleeve'];
    var W = 600;                                   // width of every design area, in design units
    var PROPS = ['dlId', 'dlMethod', 'dlName', 'dlNotes'];
    var MAX_PIXELS = 1600;                         // uploaded images are kept at most this big in the editor
    var TEXT_COLORS = [['White', '#ffffff'], ['Black', '#1c1f1b'], ['Gold', '#d4a72c'], ['Navy', '#252a46'],
                       ['Red', '#e3283a'], ['Forest green', '#1d3a2c'], ['Pink', '#f2a7bf'], ['Grey', '#8a9086']];
    var LABELS = DATA.sideLabels;

    var $ = function (id) { return document.getElementById(id); };
    var all = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
    function money(n) { return '$' + n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
    function round2(n) { return Math.round(n * 100) / 100; }
    function plural(n, one, many) { return n + ' ' + (n === 1 ? one : many); }
    function uid() { return 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
    function store(key, val) {                     // sessionStorage can be blocked: never let it break the page
        try {
            if (val === undefined) return window.sessionStorage.getItem(key);
            window.sessionStorage.setItem(key, val);
        } catch (e) { return null; }
        return null;
    }

    // ---- Catalogue index ----
    var styles = {}, catOf = {};
    DATA.catalog.forEach(function (cat) {
        cat.styles.forEach(function (s) { styles[s.id] = s; catOf[s.id] = cat; });
    });

    var state = {
        view: 'merch',          // merch | style | colour | editor
        step: 'design',         // editor: design | price
        changing: false,        // pickers opened from the editor ("Change product")
        pickCat: null, pickStyle: null, pickColor: null,
        style: null, color: null, side: 'front',
        designs: { front: null, back: null, left_sleeve: null, right_sleeve: null },
        qty: {},                // size name -> pieces
        uid: '', name: '', email: '',
        textColor: '#ffffff',
        dirty: false,
        H: W                    // height of the current design area, in design units
    };
    var files = {};             // dlId -> original File (sent to the team for printing)
    var canvas = null;
    var loadToken = 0;

    // =================================================================
    // Pickers
    // =================================================================
    function showView(view) {
        state.view = view;
        var picker = view !== 'editor';
        $('dlPicker').hidden = !picker;
        $('dlLab').hidden = picker;
        $('dlStepMerch').hidden = view !== 'merch';
        $('dlStepStyle').hidden = view !== 'style';
        $('dlStepColour').hidden = view !== 'colour';
        $('dlPill').hidden = picker;
        $('dlHeaderTitle').hidden = !(picker && state.changing);
        all('[data-carry], #dlStepMerch [data-back="editor"]').forEach(function (el) { el.hidden = !state.changing; });
        $('dlMerchSub').hidden = state.changing;
        window.scrollTo(0, 0);
        if (view === 'merch') renderMerch();
        if (view === 'style') renderStyles();
        if (view === 'colour') renderColourStep();
        if (view === 'editor') { closeSheet(); renderEditor(); setTimeout(layout, 0); }
    }

    function photoBox(url) { return '<img src="' + url + '" alt="" loading="lazy">'; }

    function card(opts) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'dl-card' + (opts.on ? ' is-on' : '');
        b.setAttribute('aria-pressed', opts.on ? 'true' : 'false');
        b.innerHTML =
            '<span class="dl-card-photo">' + photoBox(opts.photo) +
            (opts.tag ? '<span class="dl-tag' + (opts.current ? ' is-current' : '') + '"></span>' : '') +
            '<span class="dl-check" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"></path></svg></span></span>' +
            '<span class="dl-card-info"><span class="dl-card-row"><span class="dl-card-name"></span><span class="dl-card-meta" data-m1></span></span>' +
            (opts.facts ? '<span class="dl-card-meta" data-m2></span><span class="dl-card-meta" data-m3></span>' : '') + '</span>';
        b.querySelector('.dl-card-name').textContent = opts.name;
        b.querySelector('[data-m1]').textContent = opts.meta;
        if (opts.tag) b.querySelector('.dl-tag').textContent = opts.tag;
        if (opts.facts) {
            b.querySelector('[data-m2]').textContent = opts.facts;
            b.querySelector('[data-m3]').textContent = opts.colours;
        }
        b.setAttribute('aria-label', opts.name + ', ' + opts.meta);
        b.addEventListener('click', opts.click);
        return b;
    }

    function promoTag(n) { return n ? plural(n, 'promo colour', 'promo colours') : ''; }

    function renderMerch() {
        var grid = $('dlMerchGrid');
        grid.innerHTML = '';
        var currentCat = state.style ? catOf[state.style.id] : null;
        if (!state.pickCat) state.pickCat = currentCat || DATA.catalog[0] || null;
        DATA.catalog.forEach(function (cat) {
            var promo = Math.max.apply(null, cat.styles.map(function (s) { return s.promoCount; }));
            var isCurrent = state.changing && currentCat === cat;
            grid.appendChild(card({
                photo: cat.image, name: cat.name, meta: plural(cat.styles.length, 'style', 'styles'),
                tag: isCurrent ? 'Current' : promoTag(promo), current: isCurrent,
                on: state.pickCat === cat,
                click: function () { pickCategory(cat); }
            }));
        });
        var ask = document.createElement('div');
        ask.className = 'dl-ask';
        ask.innerHTML = '<strong>Looking for something else?</strong><span>Tell us what you need and we\'ll source it.</span>' +
                        '<a href="' + DATA.urls.requestProduct + '">Request a product →</a>';
        grid.appendChild(ask);
        if (!DATA.catalog.length) {
            grid.insertAdjacentHTML('afterbegin', '<p class="dl-hint">No products are ready for the Design Lab yet.</p>');
        }
    }

    function pickCategory(cat) {
        state.pickCat = cat;
        if (cat.styles.length === 1) {
            state.pickStyle = cat.styles[0];
            state.pickColor = null;
            showView('colour');
        } else {
            showView('style');
        }
    }

    function renderStyles() {
        var cat = state.pickCat;
        var grid = $('dlStyleGrid');
        grid.innerHTML = '';
        $('dlStyleSub').textContent = cat.name + ' · ' + plural(cat.styles.length, 'style', 'styles');
        if (!state.pickStyle || cat.styles.indexOf(state.pickStyle) < 0) {
            state.pickStyle = (state.style && cat.styles.indexOf(state.style) >= 0) ? state.style : cat.styles[0];
        }
        cat.styles.forEach(function (s) {
            grid.appendChild(card({
                photo: s.photo, name: s.name, meta: 'From ' + money(s.from),
                facts: s.facts || ' ', colours: plural(s.colors.length, 'colour', 'colours'),
                tag: promoTag(s.promoCount), on: state.pickStyle === s,
                click: function () { state.pickStyle = s; state.pickColor = null; showView('colour'); }
            }));
        });
    }

    function swatchGroups(style, selected, onPick) {
        var wrap = document.createElement('div');
        wrap.style.display = 'flex';
        wrap.style.flexDirection = 'column';
        wrap.style.gap = '12px';
        var promo = style.promoPct > 0 ? style.colors.filter(function (c) { return c.is_promo; }) : [];
        var rest = style.colors.filter(function (c) { return promo.indexOf(c) < 0; });
        function group(title, list, isPromo) {
            if (!list.length) return;
            var block = document.createElement('div');
            block.className = 'dl-swatch-block';
            block.innerHTML = '<p class="dl-label' + (isPromo ? ' is-promo' : '') + '"></p><div class="dl-swatches" role="group"></div>';
            block.querySelector('p').textContent = title;
            var row = block.querySelector('.dl-swatches');
            row.setAttribute('aria-label', title);
            list.forEach(function (c) {
                var b = document.createElement('button');
                b.type = 'button';
                b.className = 'dl-swatch';
                b.title = c.name;
                b.setAttribute('aria-label', c.name + (isPromo ? ', on promotion' : ''));
                b.setAttribute('aria-pressed', c === selected ? 'true' : 'false');
                b.innerHTML = '<span></span>';
                b.firstChild.style.background = c.hex;
                b.addEventListener('click', function () { onPick(c); });
                row.appendChild(b);
            });
            wrap.appendChild(block);
        }
        group('Promo colours', promo, true);
        group(promo.length ? 'More colours' : 'Colours', rest, false);
        return wrap;
    }

    function setPhoto(img, holder, color, side) {
        var url = color.sides[side] || color.sides[Object.keys(color.sides)[0]];
        if (img.getAttribute('src') !== url) img.src = url;
        holder.classList.toggle('dl-tinted', !!color.tinted);
        holder.style.setProperty('--tint', color.hex);
    }

    function renderColourStep() {
        var s = state.pickStyle;
        if (!state.pickColor || s.colors.indexOf(state.pickColor) < 0) {
            state.pickColor = (state.style === s && state.color) ? state.color : s.colors[0];
        }
        var c = state.pickColor;
        var single = catOf[s.id].styles.length === 1;
        var back = $('dlColourBack');
        back.dataset.back = single ? 'merch' : 'style';
        back.textContent = single ? '← All merch' : '← ' + catOf[s.id].name + ' styles';
        $('dlColourStyle').textContent = s.name;
        $('dlColourName').textContent = c.name;
        setPhoto($('dlColourImg'), $('dlColourPhoto'), c, 'front');
        $('dlColourImg').alt = s.name + ' in ' + c.name;
        var box = $('dlColourSwatches');
        box.innerHTML = '';
        box.appendChild(swatchGroups(s, c, function (pick) { state.pickColor = pick; renderColourStep(); }));
    }

    // Use the product picked in the pickers (keeps the design)
    function applyPick() {
        saveSide();
        state.style = state.pickStyle;
        state.color = state.pickColor;
        state.changing = false;
        if (!state.color.sides[state.side]) state.side = firstSide();
        state.dirty = state.dirty || hasArt();
        showView('editor');
        loadSide(state.side);
        updateUrl();
    }

    // =================================================================
    // Editor
    // =================================================================
    function availableSides() { return SIDES.filter(function (s) { return !!state.color.sides[s]; }); }
    function firstSide() { return availableSides()[0] || 'front'; }
    // Design area = the whole photo of every side (left, top, width, height in %).
    // The admin's "print areas" are no longer used to limit the design.
    var FULL_AREA = [0, 0, 100, 100];
    function area() { return FULL_AREA; }

    function initCanvas() {
        // fabric 5.3 sets the invalid textBaseline 'alphabetical' (browser warning on every
        // text draw); same function with the correct 'alphabetic'
        fabric.Text.prototype._setTextStyles = function (ctx, charStyle, forMeasuring) {
            ctx.textBaseline = 'alphabetic';
            if (this.path) {
                if (this.pathAlign === 'center') ctx.textBaseline = 'middle';
                else if (this.pathAlign === 'ascender') ctx.textBaseline = 'top';
                else if (this.pathAlign === 'descender') ctx.textBaseline = 'bottom';
            }
            ctx.font = this._getFontDeclaration(charStyle, forMeasuring);
        };
        fabric.Object.prototype.set({
            transparentCorners: false, cornerColor: '#ffffff', cornerStrokeColor: '#2f6fde', borderColor: '#2f6fde',
            cornerStyle: 'circle', cornerSize: window.matchMedia('(pointer: coarse)').matches ? 16 : 12, padding: 4
        });
        // Corners keep the shape (no stretching from the side handles); the top-right
        // corner is a small round "remove" button
        fabric.Object.prototype.setControlsVisibility({ mt: false, mb: false, ml: false, mr: false, tr: false });
        fabric.Object.prototype.controls.dlDelete = new fabric.Control({
            x: 0.5, y: -0.5, cursorStyle: 'pointer', sizeX: 24, sizeY: 24,
            mouseUpHandler: function (e, t) { removeItem(state.side, t.target.dlId); return true; },
            render: function (ctx, left, top) {
                ctx.save();
                ctx.translate(left, top);
                ctx.beginPath(); ctx.arc(0, 0, 11, 0, Math.PI * 2); ctx.fillStyle = '#a3401b'; ctx.fill();
                ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 2; ctx.lineCap = 'round';
                ctx.beginPath(); ctx.moveTo(-4, -4); ctx.lineTo(4, 4); ctx.moveTo(4, -4); ctx.lineTo(-4, 4); ctx.stroke();
                ctx.restore();
            }
        });
        canvas = new fabric.Canvas('dlCanvas', { preserveObjectStacking: true, selection: false, enableRetinaScaling: true });
        canvas.on('selection:created', onSelect);
        canvas.on('selection:updated', onSelect);
        canvas.on('selection:cleared', onSelect);
        canvas.on('object:modified', function () { state.dirty = true; });
    }

    function renderEditor() {
        var s = state.style, c = state.color;
        all('[data-style-name]').forEach(function (el) { el.textContent = s.name; });
        all('[data-color-name]').forEach(function (el) { el.textContent = c.name; });
        all('[data-side-name]').forEach(function (el) { el.textContent = LABELS[state.side]; });
        $('dlPillImg').src = c.sides[firstSide()];
        $('dlPillName').textContent = s.name;
        $('dlPillColor').textContent = c.name;
        $('dlPill').setAttribute('aria-label', 'Change product. Current product: ' + s.name + ', ' + c.name);
        setPhoto($('dlPhoto'), $('dlShirt'), c, state.side);
        $('dlPhoto').alt = s.name + ', ' + LABELS[state.side] + ', ' + c.name;
        $('dlArea').classList.toggle('is-light', isLight(c.hex));
        var sc = $('dlSizeChart');
        sc.hidden = !s.sizeChart;
        if (s.sizeChart) sc.href = s.sizeChart;
        var box = $('dlToolSwatches');
        box.innerHTML = '';
        box.appendChild(swatchGroups(s, c, pickEditorColour));
        renderSides();
        renderSizes();
        renderStep();
        renderArts();
    }

    function isLight(hex) {
        var h = (hex || '#ffffff').replace('#', '');
        if (h.length === 3) h = h.replace(/(.)/g, '$1$1');
        var n = parseInt(h, 16);
        var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
        return (r * 299 + g * 587 + b * 114) / 1000 > 160;
    }

    function pickEditorColour(c) {
        saveSide();
        state.color = c;
        if (!c.sides[state.side]) state.side = firstSide();
        renderEditor();
        loadSide(state.side);
        updateUrl();
    }

    function renderSides() {
        var box = $('dlSides');
        box.innerHTML = '';
        availableSides().forEach(function (side) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'dl-side';
            b.setAttribute('aria-pressed', side === state.side ? 'true' : 'false');
            b.innerHTML = '<img alt="" src="' + state.color.sides[side] + '"><span></span>' +
                          (itemsOn(side).length ? '<i aria-label="Has artwork"></i>' : '');
            b.querySelector('span').textContent = LABELS[side];
            if (state.color.tinted) { b.querySelector('img').style.background = state.color.hex; b.querySelector('img').style.mixBlendMode = 'multiply'; }
            b.addEventListener('click', function () { switchSide(side); });
            box.appendChild(b);
        });
    }

    function switchSide(side) {
        if (side === state.side) return;
        saveSide();
        state.side = side;
        renderEditor();
        loadSide(side);
    }

    // Put the photo, the design area and the canvas in place for the current size of the screen
    function layout() {
        if (state.view !== 'editor' || !canvas) return;
        var box = $('dlStageBox'), img = $('dlPhoto');
        if (!img.naturalWidth) return;
        var cs = window.getComputedStyle(box);
        var maxW = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
        var maxH = box.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
        if (maxW < 50 || maxH < 50) return;
        var r = Math.min(maxW / img.naturalWidth, maxH / img.naturalHeight);
        var w = Math.floor(img.naturalWidth * r), h = Math.floor(img.naturalHeight * r);
        img.style.width = w + 'px';
        img.style.height = h + 'px';
        var a = area();
        var aw = Math.max(20, Math.round(w * a[2] / 100)), ah = Math.max(20, Math.round(h * a[3] / 100));
        var el = $('dlArea');
        el.style.left = Math.round(w * a[0] / 100) + 'px';
        el.style.top = Math.round(h * a[1] / 100) + 'px';
        el.style.width = aw + 'px';
        el.style.height = ah + 'px';
        state.H = W * ah / aw;
        canvas.setDimensions({ width: aw, height: ah });
        canvas.setZoom(aw / W);
        canvas.calcOffset();
        canvas.requestRenderAll();
    }

    // The side on the canvas is the live one; the others are kept as JSON
    function saveSide() {
        if (!canvas || !state.style || state.loading) return;   // never save a side that is still loading
        state.designs[state.side] = canvas.toJSON(PROPS);
    }

    function loadSide(side) {
        var token = ++loadToken;
        var json = state.designs[side];
        state.loading = true;
        canvas.discardActiveObject();
        canvas.clear();
        var done = function () {
            if (token !== loadToken) return;
            state.loading = false;
            layout();
            canvas.requestRenderAll();
            renderArts();
            onSelect();
        };
        if (json && json.objects && json.objects.length) {
            canvas.loadFromJSON({ objects: json.objects }, function () {
                canvas.getObjects().forEach(function (o) { if (o.type === 'i-text') o.set({ editable: false }); });
                fontsReady(canvas.getObjects()).then(done);
            });
        } else {
            done();
        }
    }

    function fontsReady(objects) {
        if (!document.fonts || !document.fonts.load) return Promise.resolve();
        var loads = objects.filter(function (o) { return o.fontFamily; }).map(function (o) {
            return document.fonts.load('64px "' + o.fontFamily + '"').catch(function () {});
        });
        return Promise.all(loads).then(function () {
            objects.forEach(function (o) { if (o.initDimensions) { o.initDimensions(); o.setCoords(); } });
        });
    }

    // ---- Artwork (images and texts) on all sides ----
    function itemsOn(side) {
        if (side === state.side && canvas) {
            return canvas.getObjects().map(function (o) { return info(side, o, o.type === 'image' ? o.getSrc() : ''); });
        }
        var json = state.designs[side];
        return (json && json.objects ? json.objects : []).map(function (o) { return info(side, o, o.src || ''); });
    }
    function info(side, o, src) {
        return { side: side, id: o.dlId, type: o.type, method: o.dlMethod || 'print', name: o.dlName || '',
                 text: o.text || '', font: o.fontFamily || '', fill: o.fill || '', src: src };
    }
    function allItems() {
        var out = [];
        SIDES.forEach(function (s) { out = out.concat(itemsOn(s)); });
        return out;
    }
    function visibleItems() {
        var av = availableSides();
        return allItems().filter(function (i) { return av.indexOf(i.side) >= 0; });
    }
    function hasArt() { return allItems().length > 0; }

    function findJson(side, id) {
        var json = state.designs[side];
        return json && json.objects ? json.objects.filter(function (o) { return o.dlId === id; })[0] : null;
    }
    function findLive(id) { return canvas.getObjects().filter(function (o) { return o.dlId === id; })[0] || null; }

    function setMethod(side, id, method, fromPopup) {
        var obj = side === state.side ? findLive(id) : findJson(side, id);
        if (!obj) return;
        var before = obj.dlMethod || 'print';
        if (obj.set) obj.set('dlMethod', method); else obj.dlMethod = method;
        state.dirty = true;
        if (method === 'embroidery' && before !== 'embroidery' && !fromPopup) maybeEmbNote(function () { setMethod(side, id, 'print', true); });
        renderArts();
        onSelect();
    }

    function removeItem(side, id) {
        if (side === state.side) {
            var o = findLive(id);
            if (o) { canvas.remove(o); canvas.discardActiveObject(); canvas.requestRenderAll(); }
        } else if (state.designs[side]) {
            state.designs[side].objects = state.designs[side].objects.filter(function (o) { return o.dlId !== id; });
        }
        delete files[id];
        state.dirty = true;
        renderArts();
        renderSides();
        onSelect();
    }

    function focusItem(side, id) {
        if (side !== state.side) {
            switchSide(side);
            setTimeout(function () { var o = findLive(id); if (o) { canvas.setActiveObject(o); canvas.requestRenderAll(); onSelect(); } }, 120);
            return;
        }
        var o = findLive(id);
        if (o) { canvas.setActiveObject(o); canvas.requestRenderAll(); onSelect(); }
    }

    function artCard(i, withRemove) {
        var el = document.createElement('div');
        el.className = 'dl-art';
        var active = canvas && canvas.getActiveObject();
        if (active && active.dlId === i.id && i.side === state.side) el.classList.add('is-active');
        var title = i.type === 'image' ? (i.name || 'Image') : '"' + i.text + '"';
        el.innerHTML =
            '<div class="dl-art-top">' +
            '<button type="button" class="dl-art-thumb" aria-label="Select this artwork"></button>' +
            '<div class="dl-art-info"><span class="dl-art-side"></span><span class="dl-art-name"></span></div>' +
            (withRemove ? '<button type="button" class="dl-remove"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"></path></svg>Remove</button>' : '') +
            '</div>' +
            '<fieldset class="dl-methods"><legend class="visually-hidden"></legend>' +
            '<label class="dl-method"><input type="radio" value="print">Print</label>' +
            '<label class="dl-method"><input type="radio" value="embroidery">Embroidery</label></fieldset>' +
            '<p class="dl-art-note" hidden></p>';
        var thumb = el.querySelector('.dl-art-thumb');
        thumb.style.backgroundColor = state.color.hex;
        if (i.type === 'image') {
            var im = document.createElement('img');
            im.src = i.src; im.alt = '';
            thumb.appendChild(im);
        } else {
            thumb.textContent = 'T';
            thumb.style.color = i.fill || '#1c1f1b';
            thumb.style.fontFamily = '"' + i.font + '", sans-serif';
        }
        thumb.addEventListener('click', function () { focusItem(i.side, i.id); });
        el.querySelector('.dl-art-side').textContent = LABELS[i.side];
        el.querySelector('.dl-art-name').textContent = title;
        el.querySelector('legend').textContent = 'How to make the ' + LABELS[i.side] + ' artwork';
        if (i.type !== 'image') el.querySelector('.dl-methods').remove();   // text: print only, no choice
        var group = 'dl-m-' + (withRemove ? 'd-' : 'p-') + i.id;   // one radio group per list
        all('input', el).forEach(function (inp) {
            inp.name = group;
            inp.checked = inp.value === i.method;
            inp.addEventListener('change', function () { setMethod(i.side, i.id, inp.value); });
        });
        if (i.method === 'embroidery') {
            var note = el.querySelector('.dl-art-note');
            note.hidden = false;
            note.textContent = 'Embroidery adds ' + money(DATA.pricing.emb) + ' per piece for this artwork.';
        }
        var rm = el.querySelector('.dl-remove');
        if (rm) {
            rm.setAttribute('aria-label', 'Remove ' + LABELS[i.side] + ' artwork ' + title);
            rm.addEventListener('click', function () { removeItem(i.side, i.id); });
        }
        return el;
    }

    function renderArts() {
        if (!state.style) return;
        var items = visibleItems();
        var list = $('dlArts'), priceList = $('dlPriceArts');
        var keepTop = list.scrollTop, keepPriceTop = priceList.scrollTop;   // the lists scroll; keep the place
        list.innerHTML = '';
        priceList.innerHTML = '';
        items.forEach(function (i) {
            list.appendChild(artCard(i, true));
            priceList.appendChild(artCard(i, false));
        });
        list.scrollTop = keepTop;
        priceList.scrollTop = keepPriceTop;
        // A new or selected layer scrolls into view inside the list (not the whole page)
        var act = list.querySelector('.dl-art.is-active');
        if (act && (act.offsetTop < list.scrollTop || act.offsetTop + act.offsetHeight > list.scrollTop + list.clientHeight)) {
            list.scrollTop = act.offsetTop - 8;
        }
        $('dlNoArts').hidden = items.length > 0;
        $('dlEmpty').hidden = itemsOn(state.side).length > 0 || state.step !== 'design';
        var av = availableSides();
        var hiddenSides = SIDES.filter(function (s) { return av.indexOf(s) < 0 && itemsOn(s).length; });
        var note = $('dlHiddenArt');
        note.hidden = !hiddenSides.length;
        if (hiddenSides.length) {
            var names = hiddenSides.map(function (s) { return LABELS[s].toLowerCase(); }).join(' and ');
            note.textContent = 'Your ' + names + ' design is saved. This product has no ' + names +
                               ', so it\'s hidden — switch back to a product that has it and it returns.';
        }
        renderSides();
        renderPrice();
    }

    // ---- Selected artwork: phone bar + text panel ----
    function onSelect() {
        var o = canvas ? canvas.getActiveObject() : null;
        var bar = $('dlMbar');
        bar.hidden = !o || state.step !== 'design';
        if (o) {
            var isImage = o.type === 'image';   // text is print only: no Print / Embroidery choice
            $('dlMbarTitle').textContent = LABELS[state.side] + (isImage ? ' artwork · how should we make it?' : ' text');
            bar.querySelector('.dl-methods').style.display = isImage ? '' : 'none';
            all('input[name="dlMbarMethod"]').forEach(function (inp) { inp.checked = inp.value === (o.dlMethod || 'print'); });
        }
        all('.dl-art').forEach(function (el) { el.classList.remove('is-active'); });
        if (o) {
            all('#dlArts .dl-art').forEach(function (el, n) {
                var item = visibleItems()[n];
                if (item && item.id === o.dlId && item.side === state.side) el.classList.add('is-active');
            });
        }
        // A selected text fills the text panel, so it can be changed
        var editing = o && o.type === 'i-text';
        $('dlTextAdd').textContent = editing ? 'Update text' : 'Add text';
        if (editing) {
            $('dlTextInput').value = o.text;
            $('dlFont').value = o.fontFamily;
            state.textColor = o.fill;
            all('input[name="dlTextMethod"]').forEach(function (inp) { inp.checked = inp.value === (o.dlMethod || 'print'); });
            renderTextColours();
        }
    }

    // =================================================================
    // Text
    // =================================================================
    function renderTextColours() {
        var box = $('dlTextColors');
        box.innerHTML = '';
        TEXT_COLORS.forEach(function (c) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'dl-swatch';
            b.title = c[0];
            b.setAttribute('aria-label', c[0]);
            b.setAttribute('aria-pressed', c[1].toLowerCase() === String(state.textColor).toLowerCase() ? 'true' : 'false');
            b.innerHTML = '<span></span>';
            b.firstChild.style.background = c[1];
            b.addEventListener('click', function () {
                state.textColor = c[1];
                renderTextColours();
                liveText();
            });
            box.appendChild(b);
        });
    }

    // Text is always printed (no embroidery option for text)
    function textMethod() { return 'print'; }
    function selectedText() { var o = canvas.getActiveObject(); return o && o.type === 'i-text' ? o : null; }

    // Changing font / colour / method updates the selected text right away
    function liveText() {
        var o = selectedText();
        if (!o) return;
        var font = $('dlFont').value;
        fontsReady([{ fontFamily: font }]).then(function () {
            o.set({ fontFamily: font, fill: state.textColor, dlMethod: textMethod() });
            o.initDimensions(); o.setCoords();
            canvas.requestRenderAll();
            state.dirty = true;
            renderArts();
        });
    }

    function addOrUpdateText() {
        var text = $('dlTextInput').value.trim();
        var err = $('dlTextError');
        if (!text) { err.hidden = false; err.textContent = 'Please type your text first.'; $('dlTextInput').focus(); return; }
        err.hidden = true;
        var font = $('dlFont').value, method = textMethod();
        var o = selectedText();
        var wasEmb = o && o.dlMethod === 'embroidery';
        fontsReady([{ fontFamily: font }]).then(function () {
            if (o) {
                o.set({ text: text, fontFamily: font, fill: state.textColor, dlMethod: method });
                o.initDimensions();
            } else {
                // New text goes in the middle, or under the artwork that is already there
                var busy = canvas.getObjects().length > 0;
                o = new fabric.IText(text, {
                    left: W / 2, top: state.H * (busy ? 0.65 : 0.5), originX: 'center', originY: 'center',
                    fontFamily: font, fontSize: 72, fill: state.textColor, textAlign: 'center', editable: false,
                    dlId: uid(), dlMethod: method, dlName: '', dlNotes: ''
                });
                canvas.add(o);
                // The design area is the whole photo, so new text starts small enough to sit on
                // the product (max 30% of the photo wide, 12% tall); the customer can resize it
                o.scale(Math.min((W * 0.3) / o.width, (state.H * 0.12) / o.height));
            }
            var shrinkBy = Math.min((W * 0.9) / o.getScaledWidth(), (state.H * 0.9) / o.getScaledHeight());
            if (shrinkBy < 1) o.scale(o.scaleX * shrinkBy);
            o.setCoords();
            canvas.setActiveObject(o);
            canvas.requestRenderAll();
            state.dirty = true;
            renderArts();
            onSelect();
            if (method === 'embroidery' && !wasEmb) maybeEmbNote(function () { setMethod(state.side, o.dlId, 'print', true); });
            closeSheet();   // phones: close the sheet so the text is visible
        });
    }

    function openTextPanel(open) {
        var panel = $('dlTextPanel');
        panel.hidden = !open;
        $('dlTextBtn').setAttribute('aria-pressed', open ? 'true' : 'false');
        if (open) {
            if (!selectedText()) {
                $('dlTextInput').value = '';
                $('dlTextAdd').textContent = 'Add text';
            }
            renderTextColours();
            setTimeout(function () { $('dlTextInput').focus(); }, 30);
        }
    }

    // =================================================================
    // Upload your image
    // =================================================================
    var upload = { file: null };

    function resetUpload() {
        upload.file = null;
        $('dlFile').value = '';
        $('dlDrop').classList.remove('has-file');
        $('dlDropPreview').hidden = true;
        $('dlDropIcon').style.display = '';
        $('dlDropLabel').innerHTML = 'Drag your image here or <u>browse</u>';
        $('dlDropHint').textContent = 'PNG, JPG, WEBP or GIF · up to ' + DATA.maxImageMb + ' MB';
        $('dlFileError').hidden = true;
        $('dlNotes').value = '';
        all('input[name="dlUpMethod"]').forEach(function (r) { r.checked = r.value === 'print'; });
        $('dlUpEmbNote').hidden = true;
        $('dlTerms').checked = store('dlTerms') === '1';
        uploadReady();
    }

    function uploadReady() { $('dlUploadGo').disabled = !(upload.file && $('dlTerms').checked); }

    function takeFile(file) {
        var err = $('dlFileError');
        err.hidden = true;
        if (!file) return;
        if (['image/png', 'image/jpeg', 'image/webp', 'image/gif'].indexOf(file.type) < 0) {
            err.hidden = false; err.textContent = 'Please choose a PNG, JPG, WEBP or GIF image.'; return;
        }
        if (file.size > DATA.maxImageMb * 1024 * 1024) {
            err.hidden = false; err.textContent = 'This image is too big - please keep it under ' + DATA.maxImageMb + ' MB.'; return;
        }
        upload.file = file;
        var prev = $('dlDropPreview');
        prev.src = URL.createObjectURL(file);
        prev.hidden = false;
        $('dlDropIcon').style.display = 'none';
        $('dlDrop').classList.add('has-file');
        $('dlDropLabel').textContent = file.name;
        $('dlDropHint').textContent = 'Tap to choose another image';
        uploadReady();
    }

    // Keep a smaller copy in the editor (fast, light to save); the original goes to the team
    function shrink(file) {
        return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onerror = reject;
            reader.onload = function () {
                var img = new Image();
                img.onerror = reject;
                img.onload = function () {
                    var k = Math.min(1, MAX_PIXELS / Math.max(img.naturalWidth, img.naturalHeight));
                    if (k === 1 && file.type !== 'image/gif' && file.size < 3 * 1024 * 1024) { resolve(reader.result); return; }
                    var cv = document.createElement('canvas');
                    cv.width = Math.round(img.naturalWidth * k);
                    cv.height = Math.round(img.naturalHeight * k);
                    cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
                    resolve(file.type === 'image/jpeg' ? cv.toDataURL('image/jpeg', 0.92) : cv.toDataURL('image/png'));
                };
                img.src = reader.result;
            };
            reader.readAsDataURL(file);
        });
    }

    function doUpload() {
        var file = upload.file;
        if (!file || !$('dlTerms').checked) return;
        store('dlTerms', '1');
        var methodEl = document.querySelector('input[name="dlUpMethod"]:checked');
        var method = methodEl ? methodEl.value : 'print';
        var notes = $('dlNotes').value.trim();
        $('dlUploadGo').disabled = true;
        shrink(file).then(function (src) {
            fabric.Image.fromURL(src, function (img) {
                var id = uid();
                // Starts at most 30% of the photo, so it sits on the product (not over the edges)
                var k = Math.min((W * 0.3) / img.width, (state.H * 0.3) / img.height);
                img.set({
                    left: W / 2, top: state.H / 2, originX: 'center', originY: 'center', scaleX: k, scaleY: k,
                    dlId: id, dlMethod: method, dlName: file.name.slice(0, 120), dlNotes: notes
                });
                files[id] = file;
                canvas.add(img);
                canvas.setActiveObject(img);
                canvas.requestRenderAll();
                state.dirty = true;
                closeModal();
                renderArts();
                onSelect();
            });
        }).catch(function () {
            $('dlFileError').hidden = false;
            $('dlFileError').textContent = 'This image could not be read. Please try another file.';
            uploadReady();
        });
    }

    // =================================================================
    // Embroidery note: once per visit
    // =================================================================
    var embUndo = null;
    function maybeEmbNote(undo) {
        if (store('dlEmbSeen') === '1') return;
        store('dlEmbSeen', '1');
        embUndo = undo;
        openModal('dlEmb');
    }

    // =================================================================
    // Sizes and price
    // =================================================================
    function renderSizes() {
        var grid = $('dlSizes');
        grid.innerHTML = '';
        var sizes = state.color.sizes;
        grid.style.setProperty('--n', Math.min(sizes.length, 7));
        sizes.forEach(function (s) {
            var id = 'dl-qty-' + s.label.replace(/\W/g, '');
            var cell = document.createElement('div');
            cell.className = 'dl-size';
            cell.innerHTML = '<label></label><input type="text" inputmode="numeric" pattern="[0-9]*" placeholder="0" autocomplete="off">';
            var label = cell.querySelector('label'), input = cell.querySelector('input');
            label.textContent = s.label;
            label.htmlFor = id;
            input.id = id;
            input.value = state.qty[s.name] || '';
            input.classList.toggle('has-qty', !!state.qty[s.name]);
            input.addEventListener('input', function () {
                var v = input.value.replace(/[^0-9]/g, '').slice(0, 4);
                input.value = v;
                state.qty[s.name] = parseInt(v, 10) || 0;
                input.classList.toggle('has-qty', state.qty[s.name] > 0);
                renderPrice();
            });
            grid.appendChild(cell);
        });
    }

    // Tiers can share a boundary (2-5 and 5-10): the bigger tier wins, so "5+ pieces"
    // really starts at 5. Same rule as _tier_pct() in views.py.
    function tierFor(q) {
        var t = DATA.pricing.tiers, best = null;
        for (var i = 0; i < t.length; i++) {
            if (q >= t[i].min && (t[i].max === null || q <= t[i].max) && (!best || t[i].min > best.min)) best = t[i];
        }
        return best;
    }

    function quote() {
        var p = DATA.pricing, s = state.style, c = state.color;
        var items = visibleItems();
        var used = SIDES.filter(function (side) { return items.some(function (i) { return i.side === side; }); });
        // Print cost only for sides that actually have a design (no design yet = blank apparel price)
        var printCost = used.reduce(function (a, side) { return a + p.sides[side]; }, 0);
        var embItems = items.filter(function (i) { return i.method === 'embroidery'; });
        var promo = c.is_promo ? s.promoPct : 0;
        var q = 0, sub = 0;
        c.sizes.forEach(function (z) {
            var n = state.qty[z.name] || 0;
            q += n;
            sub += n * (z.price + printCost) * (1 - promo / 100);
        });
        var tier = tierFor(q), pct = tier ? tier.pct : 0;
        var total = 0;
        c.sizes.forEach(function (z) {
            var n = state.qty[z.name] || 0;
            if (n) total += n * round2((z.price + printCost) * (1 - promo / 100) * (1 - pct / 100) + p.emb * embItems.length);
        });
        var lowest = Math.min.apply(null, c.sizes.map(function (z) { return z.price; })) + printCost;
        var base = q ? (sub / q) : lowest * (1 - promo / 100);      // apparel + print, before the tier
        return { q: q, total: total, each: q ? total / q : 0, pct: pct, used: used, embItems: embItems,
                 base: base, baseEach: base * (1 - pct / 100), embEach: p.emb * embItems.length };
    }

    function renderPrice() {
        if (!state.style) return;
        var r = quote();
        all('[data-pieces]').forEach(function (el) { el.textContent = plural(r.q, 'piece', 'pieces'); });
        // Design step box
        var box = $('dlPriceBox');
        var next = DATA.pricing.tiers.filter(function (t) { return t.min > r.q; }).slice(0, 3);
        var html = '';
        if (r.q) {
            html += '<div><div class="dl-each"><strong>' + money(r.each) + '</strong><span>each</span></div>' +
                    '<span class="dl-total"><strong>' + money(r.total) + '</strong> total for ' + plural(r.q, 'piece', 'pieces') + '</span></div>';
        } else {
            html += '<div><div class="dl-each"><strong>From ' + money(r.base + r.embEach) + '</strong><span>each</span></div>' +
                    '<span class="dl-total">Enter how many you need in each size to see your price.</span></div>';
        }
        if (next.length) {
            html += '<div class="dl-tiers"><span class="dl-tiers-title">Buy more, save more</span>';
            next.forEach(function (t) {
                html += '<div class="dl-tier"><span>' + t.min + '+ pieces</span><span>' +
                        money(r.base * (1 - t.pct / 100) + r.embEach) + ' each</span><span>' +
                        (r.q ? 'add ' + (t.min - r.q) : '') + '</span></div>';
            });
            html += '</div>';
        }
        box.innerHTML = html;
        // Price step lines
        var sides = r.used.map(function (s) { return LABELS[s].toLowerCase(); }).join(' + ');
        // Apparel + print line = total minus embroidery, so the lines always add up to the total
        var baseTotal = r.total - DATA.pricing.emb * r.embItems.length * r.q;
        var lines = '<div class="dl-line"><span>' + esc(state.style.name) + (sides ? ' + print (' + sides + ')' : '') + '<small>' +
                    money(r.q ? baseTotal / r.q : r.baseEach) + ' × ' + r.q + '</small></span><span>' + money(baseTotal) + '</span></div>';
        r.embItems.forEach(function (i) {
            lines += '<div class="dl-line"><span>Embroidery · ' + LABELS[i.side] + '<small>' + money(DATA.pricing.emb) + ' × ' + r.q +
                     '</small></span><span>' + money(DATA.pricing.emb * r.q) + '</span></div>';
        });
        if (r.embItems.length) lines += '<p class="dl-hint">Embroidery is an estimate until we check your stitch count.</p>';
        lines += '<div class="dl-rule"></div>' +
                 '<div class="dl-line is-big"><span>Per piece</span><span>' + (r.q ? money(r.each) : '—') + '</span></div>' +
                 '<div class="dl-line"><span>Total for ' + plural(r.q, 'piece', 'pieces') + '</span><span>' + money(r.total) + '</span></div>';
        if (next.length && r.q) {
            lines += '<div class="dl-pricebox"><div class="dl-tiers" style="border:0;padding:0"><span class="dl-tiers-title">Buy more, save more</span>';
            next.forEach(function (t) {
                lines += '<div class="dl-tier"><span>' + t.min + '+ pieces</span><span>' + money(r.base * (1 - t.pct / 100) + r.embEach) +
                         ' each</span><span>add ' + (t.min - r.q) + '</span></div>';
            });
            lines += '</div></div>';
        }
        $('dlLines').innerHTML = lines;
        var parts = state.color.sizes.filter(function (z) { return state.qty[z.name] > 0; })
            .map(function (z) { return z.label + ' ' + state.qty[z.name]; });
        $('dlSizeSummary').textContent = parts.length ? parts.join(' · ') : 'No sizes yet';
        $('dlArrives').textContent = DATA.arrives;
    }

    function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    function renderStep() {
        var price = state.step === 'price';
        all('[data-step]', $('dlOrder')).forEach(function (el) { el.hidden = el.dataset.step !== state.step; });
        $('dlLab').classList.toggle('is-price', price);
        if (price && canvas) { canvas.discardActiveObject(); canvas.requestRenderAll(); }
        onSelect();
        $('dlEmpty').hidden = !state.style || itemsOn(state.side).length > 0 || price;
    }

    function goPrice() {
        if (!visibleItems().length) { toast('Upload an image or add text first.', true); return; }
        state.step = 'price';
        renderStep();
        renderArts();
        $('dlOrder').scrollTop = 0;
        if (window.matchMedia('(max-width: 860px)').matches) window.scrollTo(0, 0);
    }
    function goDesign() {
        state.step = 'design';
        renderStep();
        renderArts();
        setTimeout(layout, 0);
    }

    // =================================================================
    // Save / add to cart
    // =================================================================
    function getCookie(name) {
        var m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return m ? decodeURIComponent(m.pop()) : '';
    }

    function loadImage(url) {
        return new Promise(function (resolve, reject) {
            var img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = function () { resolve(img); };
            img.onerror = reject;
            img.src = url;
        });
    }

    // Design-only picture (for printing) and photo + design picture (cart / order) of one side
    function renderSideImages(side) {
        var json = state.designs[side];
        if (!json || !json.objects || !json.objects.length) return Promise.resolve(null);
        var a = area(side), c = state.color;
        return loadImage(c.sides[side]).then(function (photo) {
            var pw = photo.naturalWidth, ph = photo.naturalHeight;
            var aw = pw * a[2] / 100, ah = ph * a[3] / 100;
            var H = W * ah / aw;
            return new Promise(function (resolve) {
                var sc = new fabric.StaticCanvas(null, { width: W, height: H, enableRetinaScaling: false });
                sc.loadFromJSON({ objects: json.objects }, function () {
                    fontsReady(sc.getObjects()).then(function () {
                        sc.renderAll();
                        var print = sc.toDataURL({ format: 'png', multiplier: 3 });
                        var k = Math.min(1, 1000 / pw);
                        var cv = document.createElement('canvas');
                        cv.width = Math.round(pw * k);
                        cv.height = Math.round(ph * k);
                        var ctx = cv.getContext('2d');
                        if (c.tinted) {
                            ctx.fillStyle = c.hex;
                            ctx.fillRect(0, 0, cv.width, cv.height);
                            ctx.globalCompositeOperation = 'multiply';
                        }
                        ctx.drawImage(photo, 0, 0, cv.width, cv.height);
                        ctx.globalCompositeOperation = 'source-over';
                        var design = sc.toCanvasElement((aw * k) / W);
                        ctx.drawImage(design, pw * k * a[0] / 100, ph * k * a[1] / 100, aw * k, ah * k);
                        var preview = cv.toDataURL('image/jpeg', 0.86);
                        sc.dispose();
                        resolve({ print: print, preview: preview });
                    });
                });
            });
        });
    }

    function dataUrlToBlob(url) {
        var parts = url.split(','), mime = (parts[0].match(/:(.*?);/) || [])[1] || 'image/png';
        var bin = atob(parts[1]), arr = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        return new Blob([arr], { type: mime });
    }

    function submit(action, modalId, button) {
        var modal = $(modalId);
        var emailEl = modal.querySelector('input[type="email"]');
        var nameEl = modal.querySelector('input[type="text"]');
        var err = modal.querySelector('[data-error]');
        err.hidden = true;
        emailEl.classList.remove('is-invalid');
        var email = emailEl.value.trim();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            err.hidden = false; err.textContent = 'Please enter a valid email address.';
            emailEl.classList.add('is-invalid'); emailEl.focus();
            return;
        }
        saveSide();
        var items = visibleItems();
        if (!items.length) { closeModal(); toast('Upload an image or add text first.', true); return; }
        if (action === 'cart' && !quote().q) {
            closeModal(); goPrice(); toast('Please enter how many pieces you need in each size.', true);
            return;
        }
        state.email = email;
        state.name = nameEl.value.trim();
        var label = button.innerHTML;
        button.disabled = true;
        button.textContent = 'Saving…';

        var sides = {};
        SIDES.forEach(function (s) { if (state.designs[s] && state.designs[s].objects.length) sides[s] = { objects: state.designs[s].objects }; });
        var fd = new FormData();
        fd.append('action', action);
        fd.append('email', email);
        fd.append('name', state.name);
        fd.append('product_id', state.style.id);
        fd.append('color_id', state.color.id);
        fd.append('design_uid', state.uid);
        fd.append('sides', JSON.stringify(sides));
        var qty = {};
        state.color.sizes.forEach(function (z) { if (state.qty[z.name] > 0) qty[z.name] = state.qty[z.name]; });
        fd.append('sizes', JSON.stringify(qty));
        // Original images for printing (or the editor copy for a design reopened from a link)
        items.filter(function (i) { return i.type === 'image'; }).forEach(function (i) {
            var f = files[i.id];
            var blob = f || (i.src.indexOf('data:') === 0 ? dataUrlToBlob(i.src) : null);
            if (!blob) return;
            fd.append('uploaded_files', blob, f ? f.name : (i.name || 'image.png'));
            fd.append('uploaded_files_meta', JSON.stringify({ side: i.side, filename: f ? f.name : i.name }));
        });

        var pics = action === 'cart'
            ? Promise.all(availableSides().map(function (s) { return renderSideImages(s).then(function (r) { return [s, r]; }); }))
            : Promise.resolve([]);
        pics.then(function (list) {
            var previews = {}, prints = {};
            list.forEach(function (pair) { if (pair[1]) { previews[pair[0]] = pair[1].preview; prints[pair[0]] = pair[1].print; } });
            fd.append('previews', JSON.stringify(previews));
            fd.append('prints', JSON.stringify(prints));
            return fetch(DATA.urls.save, {
                method: 'POST', body: fd, credentials: 'same-origin',
                headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' }
            });
        }).then(function (res) {
            return res.json().catch(function () { return { success: false, error: 'Something went wrong (' + res.status + '). Please try again.' }; });
        }).then(function (res) {
            if (!res.success) {
                button.disabled = false; button.innerHTML = label;
                if (res.field === 'email') { emailEl.classList.add('is-invalid'); emailEl.focus(); }
                err.hidden = false; err.textContent = res.error || 'Something went wrong. Please try again.';
                return;
            }
            state.uid = res.uid;
            state.dirty = false;
            updateUrl();
            if (action === 'cart') {
                window.location.href = res.cart_url || DATA.urls.cart;
                return;
            }
            button.disabled = false; button.innerHTML = label;
            closeModal();
            toast('Saved! We\'ve emailed you a link to your design.');
        }).catch(function () {
            button.disabled = false; button.innerHTML = label;
            err.hidden = false; err.textContent = 'Could not save - please check your connection and try again.';
        });
    }

    // =================================================================
    // Popups, sheets, toast
    // =================================================================
    var openId = null, lastFocus = null;
    function openModal(id) {
        if (openId) closeModal(true);
        closeSheet();
        lastFocus = document.activeElement;
        openId = id;
        var m = $(id);
        m.hidden = false;
        if (id === 'dlUpload') resetUpload();
        if (id === 'dlSave' || id === 'dlCart') {
            all('[data-sync="name"]', m).forEach(function (el) { el.value = state.name; });
            all('[data-sync="email"]', m).forEach(function (el) { el.value = state.email; el.classList.remove('is-invalid'); });
            all('[data-error]', m).forEach(function (el) { el.hidden = true; });
        }
        var first = m.querySelector('input:not([type="file"]):not([type="radio"]):not([type="checkbox"]), button');
        setTimeout(function () { if (first) first.focus(); }, 30);
    }
    function closeModal(silent) {
        if (!openId) return;
        $(openId).hidden = true;
        openId = null;
        embUndo = null;
        if (!silent && lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function openSheet(name) {
        var lab = $('dlLab');
        closeSheet();
        lab.classList.add('sheet-' + name);
        $('dlSheetTitle').textContent = name === 'text' ? 'Add text' : 'Colour';
        all('.dl-tab').forEach(function (t) { t.setAttribute('aria-pressed', t.dataset.tab === name ? 'true' : 'false'); });
        if (name === 'text') openTextPanel(true);
    }
    function closeSheet() {
        var lab = $('dlLab');
        var wasText = lab.classList.contains('sheet-text');
        lab.classList.remove('sheet-color', 'sheet-text');
        all('.dl-tab[aria-pressed]').forEach(function (t) { t.setAttribute('aria-pressed', 'false'); });
        if (wasText && window.matchMedia('(max-width: 860px)').matches) $('dlTextPanel').hidden = true;
    }

    var toastTimer = null;
    function toast(msg, isError) {
        var t = document.querySelector('.dl-toast');
        if (!t) {
            t = document.createElement('div');
            t.className = 'dl-toast';
            t.setAttribute('role', 'status');
            $('dl').appendChild(t);
        }
        t.textContent = msg;
        t.classList.toggle('is-error', !!isError);
        t.hidden = false;
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { t.hidden = true; }, 3500);
    }

    // =================================================================
    // Navigation
    // =================================================================
    function openPicker() {
        saveSide();
        state.changing = true;
        state.pickCat = catOf[state.style.id];
        state.pickStyle = state.style;
        state.pickColor = state.color;
        showView('merch');
    }

    function next() {
        if (state.view === 'merch') { if (state.pickCat) pickCategory(state.pickCat); return; }
        if (state.view === 'style') { if (state.pickStyle) { state.pickColor = null; showView('colour'); } return; }
        if (state.view === 'colour') { applyPick(); return; }
        if (state.step === 'design') { goPrice(); return; }
        openModal('dlCart');
    }

    function updateUrl() {
        if (!state.style || !window.history.replaceState) return;
        var url = '/design-lab/?' + (state.uid ? 'design=' + state.uid : 'product=' + state.style.id + '&color=' + state.color.id);
        window.history.replaceState(null, '', url);
    }

    // =================================================================
    // Wire up
    // =================================================================
    function bind() {
        all('[data-url]').forEach(function (a) { if (DATA.urls[a.dataset.url]) a.href = DATA.urls[a.dataset.url]; });
        $('dlNext').addEventListener('click', next);
        $('dlPill').addEventListener('click', openPicker);
        $('dlStart').addEventListener('click', applyPick);
        all('[data-back]').forEach(function (b) {
            b.addEventListener('click', function () {
                var to = b.dataset.back;
                if (to === 'editor') { state.changing = false; showView('editor'); loadSide(state.side); }
                else if (to === 'design') goDesign();
                else showView(to);
            });
        });
        all('[data-open]').forEach(function (b) { b.addEventListener('click', function () {
            var what = b.dataset.open;
            if (what === 'upload') openModal('dlUpload');
            if (what === 'save') openModal('dlSave');
            if (what === 'cart') openModal('dlCart');
        }); });
        $('dlReview').addEventListener('click', goPrice);
        $('dlNextSide').addEventListener('click', function () {
            var av = availableSides();
            switchSide(av[(av.indexOf(state.side) + 1) % av.length]);
        });

        // Text
        $('dlTextBtn').addEventListener('click', function () { openTextPanel($('dlTextPanel').hidden); });
        $('dlTextAdd').addEventListener('click', addOrUpdateText);
        $('dlTextInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); addOrUpdateText(); } });
        $('dlFont').addEventListener('change', liveText);
        all('input[name="dlTextMethod"]').forEach(function (r) { r.addEventListener('change', function () {
            var o = selectedText();
            if (o) setMethod(state.side, o.dlId, r.value);
        }); });

        // Phone bar for the selected artwork
        all('input[name="dlMbarMethod"]').forEach(function (r) { r.addEventListener('change', function () {
            var o = canvas.getActiveObject();
            if (o) setMethod(state.side, o.dlId, r.value);
        }); });
        $('dlMbarRemove').addEventListener('click', function () {
            var o = canvas.getActiveObject();
            if (o) removeItem(state.side, o.dlId);
        });

        // Upload popup
        $('dlFile').addEventListener('change', function () { takeFile(this.files[0]); });
        var drop = $('dlDrop');
        ['dragenter', 'dragover'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add('is-over'); }); });
        ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove('is-over'); }); });
        drop.addEventListener('drop', function (e) { if (e.dataTransfer && e.dataTransfer.files[0]) takeFile(e.dataTransfer.files[0]); });
        $('dlTerms').addEventListener('change', uploadReady);
        all('input[name="dlUpMethod"]').forEach(function (r) { r.addEventListener('change', function () {
            var emb = r.value === 'embroidery' && r.checked;
            $('dlUpEmbNote').hidden = !emb;
            if (emb) store('dlEmbSeen', '1');   // the note is shown here, no second popup later
        }); });
        $('dlUpUsePrint').addEventListener('click', function () {
            all('input[name="dlUpMethod"]').forEach(function (r) { r.checked = r.value === 'print'; });
            $('dlUpEmbNote').hidden = true;
        });
        $('dlUploadGo').addEventListener('click', doUpload);

        // Embroidery note
        $('dlEmbUsePrint').addEventListener('click', function () {
            var undo = embUndo;
            closeModal();
            if (undo) undo();
        });

        // Save popups (name / email are shared by both)
        all('[data-sync]').forEach(function (el) { el.addEventListener('input', function () {
            if (el.dataset.sync === 'email') state.email = el.value.trim(); else state.name = el.value.trim();
        }); });
        $('dlSaveGo').addEventListener('click', function () { submit('save', 'dlSave', $('dlSaveGo')); });
        $('dlCartGo').addEventListener('click', function () { submit('cart', 'dlCart', $('dlCartGo')); });
        all('.dl-modal').forEach(function (m) {
            m.addEventListener('click', function (e) { if (e.target === m) closeModal(); });
            all('[data-close]', m).forEach(function (b) { b.addEventListener('click', function () { closeModal(); }); });
        });

        // Phone tab bar and sheets
        all('.dl-tab').forEach(function (t) { t.addEventListener('click', function () {
            var tab = t.dataset.tab;
            if (tab === 'product') openPicker();
            else if (tab === 'upload') openModal('dlUpload');
            else if (tab === 'save') openModal('dlSave');
            else if ($('dlLab').classList.contains('sheet-' + tab)) closeSheet();
            else openSheet(tab);
        }); });
        all('[data-close-sheet]').forEach(function (b) { b.addEventListener('click', closeSheet); });
        $('dlLab').addEventListener('click', function (e) { if (e.target === $('dlLab')) closeSheet(); });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { if (openId) closeModal(); else closeSheet(); return; }
            var tag = (e.target.tagName || '').toLowerCase();
            if ((e.key === 'Delete' || e.key === 'Backspace') && state.view === 'editor' && !openId &&
                tag !== 'input' && tag !== 'textarea' && tag !== 'select') {
                var o = canvas && canvas.getActiveObject();
                if (o) { e.preventDefault(); removeItem(state.side, o.dlId); }
            }
        });

        $('dlPhoto').addEventListener('load', layout);
        window.addEventListener('resize', layout);
        if (window.ResizeObserver) new ResizeObserver(layout).observe($('dlStageBox'));
        window.addEventListener('beforeunload', function (e) {
            if (state.dirty && hasArt()) { e.preventDefault(); e.returnValue = ''; }
        });
    }

    function start() {
        bind();
        initCanvas();
        renderTextColours();
        var s = DATA.start;
        var style = s.product ? styles[s.product] : null;
        if (style) {
            state.style = style;
            state.color = style.colors.filter(function (c) { return c.id === s.color; })[0] || style.colors[0];
            state.qty = s.sizes || {};
            if (s.design) {
                state.uid = s.design.uid;
                state.name = s.design.name;
                state.email = s.design.email;
                SIDES.forEach(function (side) {
                    var c = s.design.sides[side];
                    state.designs[side] = c && c.objects ? { objects: c.objects } : null;
                    // Older saved designs may have embroidered text; text is print only now
                    if (c && c.objects) c.objects.forEach(function (o) { if (o.type !== 'image') o.dlMethod = 'print'; });
                });
            }
            state.side = firstSide();
            showView('editor');
            loadSide(state.side);
        } else {
            showView('merch');
        }
    }

    start();
})();
