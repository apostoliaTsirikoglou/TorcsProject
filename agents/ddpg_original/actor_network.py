# -*- coding: utf-8 -*-

import tensorflow as tf
import numpy as np
import math

# Hyper Parameters
LAYER1_SIZE = 300
LAYER2_SIZE = 400
LEARNING_RATE = 1e-4
TAU = 1e-3
BATH_SIZE = 32

class Actor(object):


    def __init__(self, session, state_dim, action_dim):

        self.session = session
        self.state_dim = state_dim
        self.action_dim = action_dim

        ### Initialize target network μ′ with weights θμ′ ← θμ
        # create actor network
        self.state_input,\
        self.action_output,\
        self.net = self.create_network(state_dim, action_dim)

        # create target actor network
        self.target_state_input,\
        self.target_action_output,\
        self.target_update,\
        self.target_net = self.create_target_network(state_dim, action_dim, self.net)

        # define training rules
        self.create_training_method()

        # random weights, (μ′ with weights θμ′ ← θμ)
        init = tf.global_variables_initializer();
        self.session.run(init)

        self.update_target()
        # self.load_network()


    def create_network(self, state_dim, action_dim):
        layer1_size = LAYER1_SIZE
        layer2_size = LAYER2_SIZE

        print("while creating actor, state_dim = " + str(state_dim))

        #TODO not adapted to conv / image input

        # input
        state_input = tf.placeholder("float", [None, state_dim])

        W1_shape = [state_dim, layer1_size]
        W1 = tf.Variable(tf.random_uniform(W1_shape, -1 / math.sqrt(state_dim), 1 / math.sqrt(state_dim)))
        b1_shape = [layer1_size]
        b1 = tf.Variable(tf.random_uniform(b1_shape, -1 / math.sqrt(state_dim), 1 / math.sqrt(state_dim)))

        W2_shape = [layer1_size, layer2_size]
        W2 = tf.Variable(tf.random_uniform(W2_shape, -1 / math.sqrt(layer1_size), 1 / math.sqrt(layer1_size)))
        b2_shape = [layer2_size]
        b2 = tf.Variable(tf.random_uniform(b2_shape, -1 / math.sqrt(layer1_size), 1 / math.sqrt(layer1_size)))

        # W3 = tf.Variable(tf.random_uniform([layer2_size,action_dim],-3e-3,3e-3))
        # b3 = tf.Variable(tf.random_uniform([action_dim],-3e-3,3e-3))

        W_steer = tf.Variable(tf.random_uniform([layer2_size, 1], -1e-4, 1e-4))
        b_steer = tf.Variable(tf.random_uniform([1], -1e-4, 1e-4))

        W_accel = tf.Variable(tf.random_uniform([layer2_size, 1], -1e-4, 1e-4))
        b_accel = tf.Variable(tf.random_uniform([1], -1e-4, 1e-4))

        W_brake = tf.Variable(tf.random_uniform([layer2_size, 1], -1e-4, 1e-4))
        b_brake = tf.Variable(tf.random_uniform([1], -1e-4, 1e-4))

        layer1 = tf.nn.relu(tf.matmul(state_input, W1) + b1)
        layer2 = tf.nn.relu(tf.matmul(layer1, W2) + b2)

        #print("steer= " + str(tf.matmul(layer2, W_steer)) + " b_steer= " + str(b_steer))
        steer = tf.tanh(tf.matmul(layer2, W_steer) + b_steer)
        accel = tf.sigmoid(tf.matmul(layer2, W_accel) + b_accel)
        brake = tf.sigmoid(tf.matmul(layer2, W_brake) + b_brake)

        # action_output = tf.concat(1, [steer, accel, brake])
        action_output = tf.concat([steer, accel, brake], 1)

        return state_input, action_output, [W1, b1, W2, b2, W_steer, b_steer, W_accel, b_accel, W_brake, b_brake]

    # TODO, could original "create_network" be used for both?
    def create_target_network(self, state_dim, action_dim, net):

        state_input = tf.placeholder("float", [None, state_dim])
        ema = tf.train.ExponentialMovingAverage(decay=1 - TAU)
        target_update = ema.apply(net)
        target_net = [ema.average(x) for x in net]

        layer1 = tf.nn.relu(tf.matmul(state_input, target_net[0]) + target_net[1])
        layer2 = tf.nn.relu(tf.matmul(layer1, target_net[2]) + target_net[3])

        steer = tf.tanh(tf.matmul(layer2, target_net[4]) + target_net[5])
        accel = tf.sigmoid(tf.matmul(layer2, target_net[6]) + target_net[7])
        brake = tf.sigmoid(tf.matmul(layer2, target_net[8]) + target_net[9])

        # action_output = tf.concat(1, [steer, accel, brake])
        action_output = tf.concat([steer, accel, brake], 1)
        return state_input, action_output, target_update, target_net

    def create_training_method(self):
        self.q_gradient_input = tf.placeholder("float", [None, self.action_dim])
        self.parameters_gradients = tf.gradients(self.action_output, self.net, -self.q_gradient_input)
        # '''
        # for i, grad in enumerate(self.parameters_gradients):
        #    if grad is not None:
        #        self.parameters_gradients[i] = tf.clip_by_value(grad, -2.0,2.0)
        # '''
        self.optimizer = tf.train.AdamOptimizer(LEARNING_RATE).apply_gradients(zip(self.parameters_gradients, self.net))


    # TODO taken from ddgp torcs tensorflow... (all below!) check how they work!!!!!
    def update_target(self):
        self.session.run(self.target_update)

    def train(self, q_gradient_batch, state_batch):
        self.session.run(self.optimizer, feed_dict={
            self.q_gradient_input: q_gradient_batch,
            self.state_input: state_batch
        })

    def actions(self, state_batch):
        return self.session.run(self.action_output, feed_dict={
            self.state_input: state_batch
        })

    def action(self, state):
        # print(str(state))
        return self.session.run(self.action_output, feed_dict={
            self.state_input: [state]
        })[0]

    def target_actions(self, state_batch):
        return self.session.run(self.target_action_output, feed_dict={
            self.target_state_input: state_batch
        })

    def print_settings(self, settings_file):
        settings_text = ["\n\n==== from actor network ====" + "\n",
                         "LAYER1_SIZE = " + str(LAYER1_SIZE) + "\n",
                         "LAYER2_SIZE = " + str(LAYER2_SIZE) + "\n",
                         "LEARNING_RATE = " + str(LEARNING_RATE) + "\n",
                         "TAU = " + str(TAU) + "\n",
                         "BATH_SIZE = " + str(BATH_SIZE) + "\n"]
        for line in settings_text:
            settings_file.write(line)  # print settings to file

    """def variable(self,shape,f):
        return tf.Variable(tf.random_uniform(shape,-1/math.sqrt(f),1/math.sqrt(f)))"""

    # TODO create separate network functions (object) that works for Q, Q', u, and u'
    # TODO and then include these saving and loading functions there!
    '''
    def load_network(self):
        self.saver = tf.train.Saver()
        checkpoint = tf.train.get_checkpoint_state("saved_actor_networks")
        if checkpoint and checkpoint.model_checkpoint_path:
            self.saver.restore(self.sess, checkpoint.model_checkpoint_path)
            print "Successfully loaded:", checkpoint.model_checkpoint_path
        else:
            print "Could not find old network weights"

    def save_network(self,time_step):
        print 'save actor-network...',time_step
        self.saver.save(self.sess, 'saved_actor_networks/' + 'actor-network', global_step = time_step)
    '''