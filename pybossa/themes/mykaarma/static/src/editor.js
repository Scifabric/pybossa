import Vue from 'vue';
//var editor = require('./components/editor.vue');
//var image = require('./components/image.vue');
import Imagecrop from './components/image.vue'
import Announcementimagecrop from './components/image_announcement.vue'
new Vue({
    el: '#editorpybossa',
    //render: h => h(image)
    components: {Imagecrop, Announcementimagecrop}
});
