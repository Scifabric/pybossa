<template>
    <div>
        <div>
            <div class="file-upload-form">
                Upload an image file:
                <input type="file" @change="previewImage" accept="image/*">
            </div>
            <div id="cropit-ctn" v-if="src != null && src.length > 0">
                <img id="cropit" class="preview" :src="src"/> 
                <div class="cropping-btns">
                    <button class="btn btn-info" v-on:click="createCropper" v-bind:class="{ disabled: isCropping}">Crop</button>
                    <button v-if="isCropping" class="btn btn-info" v-on:click="cropIt">Save</button>
                </div>
            </div>
            <div id="cropit-ctn" v-else>
                <img class="preview" src="http://via.placeholder.com/675x379">
            </div>
        </div>

        <div class="blogcover">
        </div>
        <div class="form-group">
            <label for="title" class="control-label"><label for="title">Title</label></label>
            <input class="form-control" v-model="data.title" placeholder="Write a nice title" type="text">
        </div>
        <markdown-editor v-model="data.body"></markdown-editor/>
        <div class="action-btns">
            <button class="btn btn-warning" v-on:click="update">Save draft</button>
            <div v-if="canPublish">
                <button v-if="this.data.published" class="btn btn-primary" v-on:click="publish(false)">Unpublish</button>
                <button v-else class="btn btn-primary" v-on:click="publish(true)">Publish</button>
            </div>
        </div>
    </div>
</template>
<script>
import axios from 'axios'
//import VueCoreImageUpload from 'vue-core-image-upload'
import { markdownEditor } from 'vue-simplemde'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.min.css'

function createCropperVanilla(){
    var image = document.getElementById('cropit');
    console.log(image)
    var cropper = new Cropper(image, {
        aspectRatio: 16 / 9,
        movable: false,
        autoCrop: false,
    })
    return cropper
}

function cleanCropper(){
    var ctn = document.getElementById('cropit-ctn');
    var image = document.getElementById('cropit');
    image.classList.remove("preview");
    image.classList.remove("cropper-hidden");
    var child = document.getElementsByClassName("cropper-container")[0];
    ctn.removeChild(child)
}

export default {
    components: {
        //   'vue-core-image-upload': VueCoreImageUpload,
        'markdown-editor': markdownEditor,
    },
    data() {
        return {
            src: '',
            announcement_id: null,
            cropper: null,
            owner: null,
            data: {
                title: '',
                body: '',
                published: false
            },
            file_name: null,
        }
    },
    created(){
        var url = window.location.href 
        var update = false
        if (url.indexOf('/update') !== -1) {
            var tmp = url.split('/')
            console.log(tmp)
            console.log(tmp[(tmp.length -2)])
            this.announcement_id = tmp[(tmp.length -2)]
            url = '/api/announcement/' + this.announcement_id
            console.log(url)
            update = true
            document.getElementById("announcementtitle").innerHTML="Update announcement"
        }
        var options = {headers: {'Content-Type': 'application/json'}}
        var self = this
        axios({
          method:'get',
          url:url,
          headers: {'Content-Type': 'application/json'},
          data: null
        })
          .then(function(response) {
          self.owner = response.data.owner
          if (update) {
            self.data.title = response.data.title
            self.data.body = response.data.body
            self.src = response.data.media_url
            self.file_name = response.data.info.file_name
          }
          else {
            // TODO: do we need this ???
            // self.data.project_id = response.data.project.id
          }
        });

    },

    methods: {
        createCropper(){
            this.cropper = createCropperVanilla()
        },
        cropIt(){
            var self = this
            if (this.cropper === null)  this.cropper = createCropperVanilla()
            self.cropper.getCroppedCanvas();
            self.cropper.getCroppedCanvas({
                width: 160,
                height: 90,
                beforeDrawImage: function(canvas) {
                    const context = canvas.getContext('2d');

                    context.imageSmoothingEnabled = false;
                    context.imageSmoothingQuality = 'high';
                },
            });


            if (document.querySelector('input[type=file]').files.length > 0) {
                this.file_name = document.querySelector('input[type=file]').files[0].name.split(".")[0] + ".png"
            }

            // Upload cropped image to server if the browser supports `HTMLCanvasElement.toBlob`
            self.cropper.getCroppedCanvas().toBlob(function (blob) {
                var formData = new FormData();

                formData.append('file', blob, self.file_name)
                formData.append('title', self.data.title)
                formData.append('body', self.data.body)
                console.log(self.puturl)

                if (self.puturl === '/api/announcement') {
                    axios.post(self.puturl, formData).then(function(response){
                        self.data.title = response.data.title
                        self.data.body = response.data.body
                        self.announcement_id = response.data.id
                        self.src = response.data.media_url + '?' + Date.now()
                        self.cropper.destroy()
                        self.cropper = null
                    }
                    )
                }
                else {
                    axios.put(self.puturl, formData).then(function(response){
                        self.data.title = response.data.title
                        self.data.body = response.data.body
                        self.announcement_id = response.data.id
                        self.src = response.data.media_url + '?' + Date.now()
                        self.cropper.destroy()
                        self.cropper = null
                    })
                }
            });

        },
        previewImage: function(event) {
            // Reference to the DOM input element
            var input = event.target;
            // Ensure that you have a file before attempting to read it
            if (input.files && input.files[0]) {
                // create a new FileReader to read this image and convert to base64 format
                var reader = new FileReader();
                // Define a callback function to run, when FileReader finishes its job
                reader.onload = (e) => {
                    // Note: arrow function used here, so that "this.imageData" refers to the imageData of Vue component
                    // Read image as base64 and set to imageData
                    this.src = e.target.result;
                }
                // Start the reader job - read file as a data url (base64 format)
                reader.readAsDataURL(input.files[0]);
            }
        },

        imageuploaded(res) {
            if(res.media_url !== '' && res.media_url !== undefined) {
                this.src = res.media_url
            }
            this.data.title = res.title
            this.data.body = res.body
            this.announcement_id = res.id
        },
        update(){
            var self = this
            if (this.puturl === '/api/announcement') {
                axios.post(this.puturl, this.data).then(function(response){
                    console.log(response)
                    if (response.data.media_url !== '' && response.data.media_url !== null) {
                        self.src = response.data.media_url
                    }
                    self.data.title = response.data.title
                    self.data.body = response.data.body
                    self.announcement_id = response.data.id

                })
        }
        else axios.put(this.puturl, this.data).then(function(response){console.log(response)})
    },
    publish(flag){
        this.data.published = flag
        axios.put(this.puturl, this.data).then(function(response){console.log(response)})
    }
},
    computed: {
        isCropping(){
            if (this.cropper !== null) return true
            else return false
        },
        puturl(){
            if (this.announcement_id) return '/api/announcement/' + this.announcement_id
            else return '/api/announcement'
        },
            canPublish(){
                if (this.data.title === '' || this.data.body === '') return false
                else return true
            }
    }
}
</script>
<style>
.blogcover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.g-core-image-upload-btn {
    position: absolute !important;
}

.action-btns {
    display: flex;
    justify-content: space-between;
}

#cropit {
    max-width: 100%;
}
.cropit-ctn {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}
</style>
