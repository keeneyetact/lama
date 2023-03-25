import React, { useEffect, useState } from 'react'
import { useRecoilState, useRecoilValue, useSetRecoilState } from 'recoil'
import Button from '../shared/Button'
import { fileState, gifImageState, toastState } from '../../store/Atoms'
import { makeGif } from '../../adapters/inpainting'
import Modal from '../shared/Modal'
import { LoadingIcon } from '../shared/Toast'
import { downloadImage } from '../../utils'
import emitter from '../../event'
import { PluginName } from '../Plugins/Plugins'

interface Props {
  renders: HTMLImageElement[]
}

const MakeGIF = (props: Props) => {
  const { renders } = props
  const [gifImg, setGifImg] = useRecoilState(gifImageState)
  const file = useRecoilValue(fileState)
  const setToastState = useSetRecoilState(toastState)
  const [show, setShow] = useState(false)

  const handleOnClose = () => {
    setShow(false)
  }

  const handleDownload = () => {
    if (gifImg) {
      const name = file.name.replace(/\.[^/.]+$/, '.gif')
      downloadImage(gifImg.src, name)
    }
  }

  useEffect(() => {
    emitter.on(PluginName.MakeGIF, async () => {
      if (renders.length === 0) {
        setToastState({
          open: true,
          desc: 'No render found',
          state: 'error',
          duration: 2000,
        })
        return
      }

      setShow(true)
      setGifImg(null)
      try {
        const gif = await makeGif(
          file,
          renders[renders.length - 1],
          file.name,
          file.type
        )
        if (gif) {
          setGifImg(gif)
        }
      } catch (e: any) {
        setToastState({
          open: true,
          desc: e.message ? e.message : e.toString(),
          state: 'error',
          duration: 2000,
        })
        setShow(false)
      }
    })
    return () => {
      emitter.off(PluginName.MakeGIF)
    }
  }, [setGifImg, renders, file, setShow])

  return (
    <Modal
      onClose={handleOnClose}
      title="GIF"
      className="modal-setting"
      show={show}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {gifImg ? (
          <img src={gifImg.src} style={{ borderRadius: 8 }} alt="gif" />
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <LoadingIcon />
            Generating GIF...
          </div>
        )}

        {gifImg && (
          <div
            style={{
              display: 'flex',
              width: '100%',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <Button onClick={handleDownload} border>
              Download
            </Button>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default MakeGIF
