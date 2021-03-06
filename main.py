import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))

############################
# Funcs for Tensorboard
############################
def variable_summaries(var):
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
    tf.summary.scalar('stddev', stddev)
    tf.summary.scalar('max', tf.reduce_max(var))
    tf.summary.scalar('min', tf.reduce_min(var))
    tf.summary.histogram('histogram', var)
############################

def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    tf.saved_model.loader.load(sess, ['vgg16'], vgg_path)
    graph = tf.get_default_graph()
    image_input = graph.get_tensor_by_name('image_input:0')
    keep_prob = graph.get_tensor_by_name('keep_prob:0')
    layer3_out = graph.get_tensor_by_name('layer3_out:0')
    layer4_out = graph.get_tensor_by_name('layer4_out:0')
    layer7_out = graph.get_tensor_by_name('layer7_out:0')
    
    return image_input, keep_prob, layer3_out, layer4_out, layer7_out
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    #vgg_layer3_out = tf.placeholder(tf.float32, [None, 56, 56, 256])
    #vgg_layer4_out = tf.placeholder(tf.float32, [None, 28, 28, 512])
    #vgg_layer7_out = tf.placeholder(tf.float32, [None, 1, 1, 4096])
    '''
    vgg_3 ...vgg_4 ...vgg_7 -> 1x1 -(4)-> layer_8
      |         |                       |
      |          ------------> 1x1 -- add
      |                                 |
      |                                 v (4)
      |                               layer_9
      |                                 |
      -----------------------> 1x1 -- add
                                        |
                                        v (16)
                                      layer_10
    '''

    conv1x1 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, strides=(1,1), padding='same',
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.01))

    #tf.Print(conv1x1, [tf.shape(conv1x1)[1:3]])

    layer_8 = tf.layers.conv2d_transpose(conv1x1, num_classes, 4, strides=(2, 2), padding='same', name='layer_8',
                                         kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                         kernel_initializer=tf.random_normal_initializer(stddev=0.01))

    conv1x1 = tf.layers.conv2d(vgg_layer4_out, num_classes, 1, strides=(1,1), padding='same',
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.01))
    output = tf.add(conv1x1, layer_8)

    layer_9 = tf.layers.conv2d_transpose(output, num_classes, 4, strides=(2, 2), padding='same', name='layer_9',
                                         kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                         kernel_initializer=tf.random_normal_initializer(stddev=0.01))

    conv1x1 = tf.layers.conv2d(vgg_layer3_out, num_classes, 1, strides=(1,1), padding='same',
                               kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                               kernel_initializer=tf.random_normal_initializer(stddev=0.01))
    output = tf.add(conv1x1, layer_9)

    layer_10 = tf.layers.conv2d_transpose(output, num_classes, 16, strides=(8, 8), padding='same', name='layer_10',
                                          kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3),
                                          kernel_initializer=tf.random_normal_initializer(stddev=0.01))

    return layer_10
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    logits = tf.reshape(nn_last_layer, (-1, num_classes))
    labels = tf.reshape(correct_label, (-1, num_classes))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels))
    #tf.summary.scalar('cross_entropy', cross_entropy_loss)
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(cross_entropy_loss)
    #tf.summary.scalar('train', train_op)

    return logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """

    # TODO: Implement function
    sess.run(tf.global_variables_initializer())

    keep_prob_val = 0.5
    learning_rate_val = 5*1e-4
    for i in range(epochs):
        minloss = 100
        for image, label in get_batches_fn(batch_size):
            # Training
            feed_dict = {input_image:image,
                         correct_label:label,
                         keep_prob:keep_prob_val,
                         learning_rate:learning_rate_val}
            _, loss = sess.run([train_op, cross_entropy_loss], feed_dict=feed_dict)
            #_, summary = sess.run([merged], feed_dict=feed_dict)
        #train_writer.add_summary(summary, i)
            if minloss > loss:
                minloss = loss
                print('epoch %i, loss: %.3f' % (i, loss))
tests.test_train_nn(train_nn)


def run():
    epochs = 50#10
    batch_size = 5#1
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:

        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        correct_label = tf.placeholder(tf.int32, [None, None, None, num_classes], name='label')
        learning_rate = tf.placeholder(tf.float32, name='learning_rate')

        input_image, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)
        nn_last_layer = layers(layer3_out, layer4_out, layer7_out, num_classes)
        logits, train_op, cross_entropy = optimize(nn_last_layer, correct_label, learning_rate, num_classes)

        # Tensorboard
        #merged = tf.summary.merge_all()
        #train_writer = tf.summary.FileWriter('log/train', sess.graph)

        # TODO: Train NN using the train_nn function
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy,
                 input_image, correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        saver = tf.train.Saver()
        saver.save(sess, 'checkpoints/model.ckpt')
        saver.export_meta_graph('checkpoints/model.meta')
        tf.train.write_graph(sess.graph_def, './checkpoints/', 'model.pb', False)

        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
