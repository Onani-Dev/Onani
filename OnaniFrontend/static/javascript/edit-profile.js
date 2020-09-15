/*
 * @Author: Blakeando
 * @Date:   2020-09-14 00:47:49
 * @Last Modified by:   Blakeando
 * @Last Modified time: 2020-09-15 17:30:40
 */
'use strict';



$uploadCrop = $('#profile-settings-profile-picture').croppie({
  enableExif: true,
  viewport: {
    width: 150,
    height: 150,
    type: 'square'
  },
  boundary: {
    width: 300,
    height: 300
  }
});

