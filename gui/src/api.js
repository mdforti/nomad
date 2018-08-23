import { apiBase } from './config'

class Upload {
  constructor(json) {
    console.debug('Created local upload for ' + json.upload_id)
    Object.assign(this, json)
  }

  uploadFile(file) {
    console.assert(this.presigned_url)
    console.debug(`Upload ${file} to ${this.presigned_url}.`)
    return fetch(this.presigned_url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/gzip'
      },
      body: file
    }).then(() => {
      console.log(`Uploaded ${file} to ${this.upload_id}.`)
      return this
    }).catch(error => {
      console.error(`Could not upload ${file} to ${this.presigned_url}: ${error}.`)
      return this
    })
  }

  update() {
    return fetch(`${apiBase}/uploads/${this.upload_id}`)
      .then(response => response.json())
      .then(uploadJson => {
        Object.assign(this, uploadJson)
        return this
      })
  }
}

function createUpload() {
  console.debug('Request new upload.')
  return fetch(`${apiBase}/uploads`, {method: 'POST'})
    .then(response => response.json())
    .then(uploadJson => new Upload(uploadJson))
}

function getUploads() {
  return fetch(`${apiBase}/uploads`)
    .then(response => response.json())
    .then(uploadsJson => uploadsJson.map(uploadJson => new Upload(uploadJson)))
}

const api = {
  createUpload: createUpload,
  getUploads: getUploads
};

export default api;